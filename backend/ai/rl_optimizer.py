"""
Reinforcement Learning Risk Optimizer
======================================
Uses Deep Q-Learning (DQN) to learn optimal contract configurations
that minimize dispute risk over time.

Components:
1. RiskEnvironment - Contract state environment
2. DQN Model - PyTorch neural network
3. Experience Replay Buffer
4. Training Loop
"""

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import deque, namedtuple

logger = logging.getLogger(__name__)

# Lazy-loaded Bayesian engine
_bayesian_engine = None

def _get_bayesian_engine():
    global _bayesian_engine
    if _bayesian_engine is None:
        try:
            import sys
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            from dispute_predictor.bayesian_engine import get_bayesian_engine
            _bayesian_engine = get_bayesian_engine()
        except Exception as e:
            logger.warning(f"Bayesian engine unavailable in RL optimizer: {e}")
    return _bayesian_engine

# Model save path
MODEL_DIR = Path(__file__).parent / 'rl_models'
MODEL_PATH = MODEL_DIR / 'contract_optimizer.pth'
MODEL_DIR.mkdir(exist_ok=True)

# Experience tuple
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])


# ═══════════════════════════════════════════════════════════════
# Contract Risk Environment
# ═══════════════════════════════════════════════════════════════

class RiskEnvironment:
    """
    Contract negotiation environment for RL.

    State: [price, delivery_days, liability_cap, payment_terms, termination_penalty, force_majeure]
    Action: Discrete actions to modify contract clauses
    Reward: -dispute_risk (negative, so minimize risk = maximize reward)
    """

    def __init__(self):
        self.state_dim = 6  # 6 contract parameters
        self.action_dim = 11  # 11 possible actions

        self.action_mapping = [
            'increase_price', 'decrease_price',
            'increase_delivery', 'decrease_delivery',
            'increase_liability', 'decrease_liability',
            'increase_payment', 'decrease_payment',
            'increase_penalty', 'decrease_penalty',
            'toggle_force_majeure'
        ]

        self.reset()

    def reset(self) -> np.ndarray:
        """Reset to initial random contract state"""
        self.state = np.array([
            np.random.uniform(80, 150),   # price
            np.random.uniform(20, 60),    # delivery_days
            np.random.uniform(0.2, 0.8),  # liability_cap
            np.random.uniform(30, 90),    # payment_terms
            np.random.uniform(5, 20),     # termination_penalty
            np.random.randint(0, 2),      # force_majeure (0 or 1)
        ], dtype=np.float32)

        return self.state.copy()

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute action and return (next_state, reward, done, info)
        """
        # Apply action
        self.state = self._apply_action(action)

        # Calculate reward (negative dispute risk)
        dispute_risk = self._calculate_dispute_risk()
        reward = -dispute_risk

        # Episode ends after one step (can extend to multi-step episodes)
        done = False

        info = {'dispute_risk': dispute_risk}

        return self.state.copy(), reward, done, info

    def _apply_action(self, action: int) -> np.ndarray:
        """Apply action to state"""
        new_state = self.state.copy()
        action_name = self.action_mapping[action]

        if action_name == 'increase_price':
            new_state[0] = min(200, new_state[0] + 10)
        elif action_name == 'decrease_price':
            new_state[0] = max(50, new_state[0] - 10)
        elif action_name == 'increase_delivery':
            new_state[1] = min(90, new_state[1] + 5)
        elif action_name == 'decrease_delivery':
            new_state[1] = max(10, new_state[1] - 5)
        elif action_name == 'increase_liability':
            new_state[2] = min(1.0, new_state[2] + 0.1)
        elif action_name == 'decrease_liability':
            new_state[2] = max(0.1, new_state[2] - 0.1)
        elif action_name == 'increase_payment':
            new_state[3] = min(120, new_state[3] + 10)
        elif action_name == 'decrease_payment':
            new_state[3] = max(10, new_state[3] - 10)
        elif action_name == 'increase_penalty':
            new_state[4] = min(30, new_state[4] + 5)
        elif action_name == 'decrease_penalty':
            new_state[4] = max(0, new_state[4] - 5)
        elif action_name == 'toggle_force_majeure':
            new_state[5] = 1 - new_state[5]

        return new_state

    def _calculate_dispute_risk(self) -> float:
        """
        Calculate dispute risk using the real 60-node Bayesian engine.

        Signal mappings are bidirectional — extreme values in either direction
        increase risk, so the RL agent learns a realistic optimum rather than
        pushing every parameter to its floor/ceiling.
        """
        price, delivery, liability, payment, penalty, force_maj = self.state

        engine = _get_bayesian_engine()
        if engine is not None:
            # LIABILITY: sweet-spot is 0.10–0.30 (10-30% of contract value)
            # Too low (<0.10) → unenforceable/ambiguous → high ContractAmbiguity
            # Too high (>0.50) → excessive exposure → high LiabilityExposure
            lib = float(liability)
            if lib < 0.10:
                liability_ambiguity = 0.80   # uncapped = very ambiguous
            elif lib <= 0.30:
                liability_ambiguity = 0.05 + (0.30 - lib) * 0.5   # ideal zone
            else:
                liability_ambiguity = min(0.9, (lib - 0.30) * 1.2)  # over-exposure

            liability_exposure = max(0.0, min(0.9, (lib - 0.15) * 1.5)) if lib > 0.15 else 0.0

            # PAYMENT: 30–60 days is normal; <20 days → cash flow stress; >75 days → default risk
            pay = float(payment)
            if pay < 20:
                payment_risk = 0.60   # unrealistically fast → signals cash-flow problems
            elif pay <= 60:
                payment_risk = max(0.0, (pay - 30) / 120)   # low risk in normal range
            else:
                payment_risk = min(0.9, (pay - 60) / 60)    # rising default risk

            # DELIVERY: sweet-spot 20–60 days; <15 days → impossible → high delay risk
            delv = float(delivery)
            if delv < 15:
                delivery_risk = 0.80  # unrealistic timeline → near-certain delay
            elif delv <= 45:
                delivery_risk = max(0.0, (45 - delv) / 120)   # low risk, realistic buffer
            else:
                delivery_risk = min(0.9, (delv - 45) / 75)    # longer = more delay risk

            # TERMINATION PENALTY: 0% → no deterrent → higher renegotiation risk
            # >15% → excessive → increases dispute risk
            pen = float(penalty)
            term_risk = 0.30 if pen == 0 else (max(0.0, min(0.9, abs(pen - 7.5) / 20)))

            signals = {
                'ContractAmbiguity': max(0.0, min(0.9, liability_ambiguity)),
                'LiabilityExposure': max(0.0, min(0.9, liability_exposure)),
                'PaymentDefaultRisk': max(0.0, min(0.9, payment_risk)),
                'SupplierDelay': max(0.0, min(0.9, delivery_risk)),
                'TerminationRisk': max(0.0, min(0.9, term_risk)),
            }
            if force_maj == 0:
                signals['ContractAmbiguity'] = min(0.9, signals['ContractAmbiguity'] + 0.20)

            result = engine.compute_dispute_probability(signals)
            return result['dispute_probability']

        # Heuristic fallback only if Bayesian engine unavailable
        risk = 0.20
        lib = float(liability)
        if lib > 0.40:
            risk += (lib - 0.40) * 0.5
        if lib < 0.10:
            risk += 0.30
        pay = float(payment)
        if pay < 20:
            risk += 0.25
        elif pay > 70:
            risk += (pay - 70) * 0.004
        delv = float(delivery)
        if delv < 15:
            risk += 0.35
        elif delv > 50:
            risk += (delv - 50) * 0.004
        if force_maj == 0:
            risk += 0.15
        return min(0.99, risk)


# ═══════════════════════════════════════════════════════════════
# DQN Model
# ═══════════════════════════════════════════════════════════════

class DQNModel(nn.Module):
    """Deep Q-Network for contract risk optimization"""

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


# ═══════════════════════════════════════════════════════════════
# Experience Replay Buffer
# ═══════════════════════════════════════════════════════════════

class ReplayBuffer:
    """Experience replay buffer for DQN"""

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, experience: Experience):
        self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Experience]:
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)


# ═══════════════════════════════════════════════════════════════
# DQN Agent
# ═══════════════════════════════════════════════════════════════

class DQNAgent:
    """DQN agent for contract risk optimization"""

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_capacity: int = 10000
    ):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

        # Q-networks
        self.policy_net = DQNModel(state_dim, action_dim).to(self.device)
        self.target_net = DQNModel(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.replay_buffer = ReplayBuffer(buffer_capacity)

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """Select action using epsilon-greedy policy"""
        if training and random.random() < self.epsilon:
            return random.randrange(self.action_dim)

        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def store_experience(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        exp = Experience(state, action, reward, next_state, done)
        self.replay_buffer.push(exp)

    def train_step(self, batch_size: int = 64) -> float:
        """Perform one training step"""
        if len(self.replay_buffer) < batch_size:
            return 0.0

        # Sample batch
        experiences = self.replay_buffer.sample(batch_size)
        batch = Experience(*zip(*experiences))

        # Convert to tensors
        state_batch = torch.FloatTensor(np.array(batch.state)).to(self.device)
        action_batch = torch.LongTensor(batch.action).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(batch.reward).to(self.device)
        next_state_batch = torch.FloatTensor(np.array(batch.next_state)).to(self.device)
        done_batch = torch.FloatTensor(batch.done).to(self.device)

        # Current Q-values
        current_q = self.policy_net(state_batch).gather(1, action_batch).squeeze()

        # Target Q-values
        with torch.no_grad():
            next_q = self.target_net(next_state_batch).max(1)[0]
            target_q = reward_batch + (1 - done_batch) * self.gamma * next_q

        # Compute loss
        loss = F.mse_loss(current_q, target_q)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return loss.item()

    def update_target_network(self):
        """Copy policy network to target network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save_model(self, path: str):
        """Save model to disk"""
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model from disk"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint.get('epsilon', self.epsilon_end)
        logger.info(f"Model loaded from {path}")


# ═══════════════════════════════════════════════════════════════
# Training Loop
# ═══════════════════════════════════════════════════════════════

def train_rl_optimizer(
    num_episodes: int = 1000,
    batch_size: int = 64,
    target_update_freq: int = 10
) -> Tuple[DQNAgent, List[Dict]]:
    """
    Train RL optimizer.

    Returns:
        (trained_agent, training_history)
    """
    env = RiskEnvironment()
    agent = DQNAgent(env.state_dim, env.action_dim)
    history = []

    logger.info(f"Starting RL training for {num_episodes} episodes...")

    for episode in range(num_episodes):
        state = env.reset()
        total_reward = 0
        steps = 0
        losses = []

        # Run episode
        for step in range(10):  # Max 10 steps per episode
            action = agent.select_action(state, training=True)
            next_state, reward, done, info = env.step(action)

            agent.store_experience(state, action, reward, next_state, done)
            total_reward += reward
            steps += 1

            # Train
            loss = agent.train_step(batch_size)
            if loss > 0:
                losses.append(loss)

            state = next_state

            if done:
                break

        # Update target network
        if (episode + 1) % target_update_freq == 0:
            agent.update_target_network()

        # Log progress
        avg_loss = np.mean(losses) if losses else 0.0
        history.append({
            'episode': episode + 1,
            'reward': total_reward,
            'steps': steps,
            'loss': avg_loss,
            'epsilon': agent.epsilon,
            'dispute_risk': info.get('dispute_risk', 0),
        })

        if (episode + 1) % 100 == 0:
            logger.info(
                f"Episode {episode + 1}/{num_episodes}: "
                f"Reward={total_reward:.3f}, Loss={avg_loss:.4f}, "
                f"Epsilon={agent.epsilon:.3f}"
            )

    logger.info("RL training completed!")

    # Save trained model
    agent.save_model(str(MODEL_PATH))

    return agent, history


# ═══════════════════════════════════════════════════════════════
# Global Cached Agent
# ═══════════════════════════════════════════════════════════════

_CACHED_AGENT: Optional[DQNAgent] = None


def get_or_load_agent(force_retrain: bool = False) -> DQNAgent:
    """
    Get cached agent or load from disk. If no model exists, train a new one.

    Args:
        force_retrain: If True, train a new model even if one exists

    Returns:
        Trained DQNAgent
    """
    global _CACHED_AGENT

    if not force_retrain and _CACHED_AGENT is not None:
        return _CACHED_AGENT

    env = RiskEnvironment()
    agent = DQNAgent(env.state_dim, env.action_dim)

    # Try to load existing model
    if not force_retrain and MODEL_PATH.exists():
        try:
            agent.load_model(str(MODEL_PATH))
            logger.info("Loaded trained RL model from disk")
        except Exception as e:
            logger.warning(f"Failed to load model: {e}. Training new model...")
            agent, _ = train_rl_optimizer(num_episodes=1000)
    else:
        logger.info("No trained model found. Training new model...")
        agent, _ = train_rl_optimizer(num_episodes=1000)

    _CACHED_AGENT = agent
    return agent


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

def optimize_contract_with_rl(
    initial_contract: Dict[str, Any],
    trained_agent: DQNAgent = None
) -> Dict[str, Any]:
    """
    Optimize contract using trained RL agent.

    Args:
        initial_contract: Dict with keys: price, delivery_days, etc.
        trained_agent: Pre-trained DQNAgent (if None, will train new)

    Returns:
        {
            'optimized_contract': Dict,
            'dispute_risk': float,
            'actions_taken': List[str],
        }
    """
    env = RiskEnvironment()

    # Set initial state
    env.state = np.array([
        initial_contract.get('price', 100),
        initial_contract.get('delivery_days', 30),
        initial_contract.get('liability_cap', 0.5),
        initial_contract.get('payment_terms', 60),
        initial_contract.get('termination_penalty', 10),
        initial_contract.get('force_majeure', 1),
    ], dtype=np.float32)

    # Capture initial risk before any changes
    initial_risk = env._calculate_dispute_risk()

    # Run optimization: greedy search — pick the action that lowers risk most each step
    actions_taken = []

    for _ in range(30):  # Max 30 optimization steps — exhaust all greedy improvements
        current_risk = env._calculate_dispute_risk()
        best_action = None
        best_risk = current_risk

        # Try all 11 actions, pick the one that minimises risk
        for a in range(env.action_dim):
            saved_state = env.state.copy()
            candidate_state = env._apply_action(a)
            env.state = candidate_state
            candidate_risk = env._calculate_dispute_risk()
            env.state = saved_state  # restore
            if candidate_risk < best_risk:
                best_risk = candidate_risk
                best_action = a

        if best_action is None:
            break  # No improvement possible — converged

        # Apply the best action permanently
        env.state = env._apply_action(best_action)
        actions_taken.append(env.action_mapping[best_action])

    final_state = env.state
    final_risk = env._calculate_dispute_risk()

    # Build optimized contract
    optimized = {
        'price': float(final_state[0]),
        'delivery_days': int(final_state[1]),
        'liability_cap': round(float(final_state[2]), 2),
        'payment_terms': int(final_state[3]),
        'termination_penalty': float(final_state[4]),
        'force_majeure': int(final_state[5]),
    }

    return {
        'optimized_contract': optimized,
        'dispute_risk': final_risk,
        'initial_dispute_risk': initial_risk,
        'risk_reduction': round(initial_risk - final_risk, 4),
        'actions_taken': actions_taken,
    }
