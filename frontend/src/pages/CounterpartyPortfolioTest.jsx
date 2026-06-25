import { useEffect } from 'react';

const CounterpartyPortfolioTest = () => {
  useEffect(() => {
    console.log('CounterpartyPortfolioTest component mounted');
  }, []);

  return (
    <div style={{ padding: '2rem' }}>
      <h1>Counterparty Portfolio Risk Heatmap - Test</h1>
      <p>If you can see this, the route is working correctly.</p>
      <p>The actual component will load here once we fix any issues.</p>
    </div>
  );
};

export default CounterpartyPortfolioTest;
