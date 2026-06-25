"""
Train RL Contract Optimizer
============================
Standalone script to train the RL model for contract risk optimization.

Usage:
    python train_rl.py [--episodes 1000] [--batch-size 64]
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

import django
django.setup()

from ai.rl_optimizer import train_rl_optimizer, MODEL_PATH
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Train RL Contract Optimizer')
    parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size for training')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("RL Contract Optimizer Training")
    logger.info("=" * 60)
    logger.info(f"Episodes: {args.episodes}")
    logger.info(f"Batch Size: {args.batch_size}")
    logger.info(f"Model will be saved to: {MODEL_PATH}")
    logger.info("=" * 60)

    # Train the model
    agent, history = train_rl_optimizer(
        num_episodes=args.episodes,
        batch_size=args.batch_size
    )

    logger.info("=" * 60)
    logger.info("Training Summary:")
    logger.info(f"  Final Epsilon: {agent.epsilon:.4f}")
    logger.info(f"  Total Episodes: {len(history)}")

    if history:
        final_10 = history[-10:]
        avg_reward = sum(h['reward'] for h in final_10) / len(final_10)
        avg_risk = sum(h['dispute_risk'] for h in final_10) / len(final_10)
        logger.info(f"  Avg Reward (last 10): {avg_reward:.3f}")
        logger.info(f"  Avg Dispute Risk (last 10): {avg_risk:.3f}")

    logger.info(f"  Model saved to: {MODEL_PATH}")
    logger.info("=" * 60)
    logger.info("Training completed successfully!")


if __name__ == '__main__':
    main()
