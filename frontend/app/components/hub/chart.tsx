import { useEffect, useState } from 'react';
import type { TransactionDataResponse } from '~/types/TransactionDataResponse';

interface ChartProps {
  data: TransactionDataResponse;
}

export default function TransactionChart({ data }: ChartProps) {
  const [EChartsComponent, setEChartsComponent] = useState<any>(null);

  useEffect(() => {
    // Dynamically import ReactECharts on the client side only
    import('echarts-for-react').then((module) => {
      setEChartsComponent(() => module.default);
    });
  }, []);

  // Transform data for ECharts
  const transactions = data.transactions || [];
  
  // Group transactions by month and category
  const groupedData = transactions.reduce((acc, transaction) => {
    const date = new Date(transaction.created_at);
    const period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const category = transaction.code || 'Other';
    const amount = transaction.amount || 0;

    if (!acc[period]) {
      acc[period] = {};
    }
    if (!acc[period][category]) {
      acc[period][category] = 0;
    }
    acc[period][category] += amount;
    return acc;
  }, {} as Record<string, Record<string, number>>);

  // Convert grouped data to ECharts format
  const periods = Object.keys(groupedData).sort();
  const categories = [...new Set(
    Object.values(groupedData).flatMap(periodData => Object.keys(periodData))
  )];

  const series = categories.map(category => ({
    name: category,
    type: 'bar',
    stack: 'total',
    data: periods.map(period => groupedData[period][category] || 0)
  }));

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: categories
    },
    xAxis: {
      type: 'category',
      data: periods
    },
    yAxis: {
      type: 'value'
    },
    series
  };

  if (!EChartsComponent) {
    return <div className="h-[500px] flex items-center justify-center">Loading chart...</div>;
  }

  return <EChartsComponent option={option} style={{ height: '500px' }} />;
}