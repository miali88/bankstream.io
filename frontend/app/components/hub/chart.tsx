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
  
  // Group transactions by month and type (expense/revenue)
  const groupedData = transactions.reduce((acc, transaction) => {
    const date = new Date(transaction.created_at);
    const period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    const amount = (transaction.amount || 0) / 100; // Divide by 100 to convert from cents
    
    if (!acc[period]) {
      acc[period] = {
        expenses: 0,
        revenue: 0
      };
    }
    
    // Categorize as expense or revenue based on amount
    if (amount < 0) {
      acc[period].expenses += Math.abs(amount); // Convert to positive for display
    } else {
      acc[period].revenue += amount;
    }
    
    return acc;
  }, {} as Record<string, { expenses: number; revenue: number }>);

  // Convert grouped data to ECharts format
  const periods = Object.keys(groupedData).sort();
  const expensesData = periods.map(period => groupedData[period].expenses);
  const revenueData = periods.map(period => groupedData[period].revenue);

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const period = params[0].axisValue;
        const expenses = groupedData[period].expenses.toFixed(2);
        const revenue = groupedData[period].revenue.toFixed(2);
        return `${period}<br/>Revenue: ${revenue}<br/>Expenses: ${expenses}`;
      }
    },
    legend: {
      data: ['Revenue', 'Expenses']
    },
    xAxis: {
      type: 'category',
      data: periods,
      axisLabel: {
        formatter: (value: string) => {
          const [year, month] = value.split('-');
          const date = new Date(parseInt(year), parseInt(month) - 1);
          return date.toLocaleString('default', { month: 'short' });
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => {
          return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(value);
        }
      }
    },
    series: [
      {
        name: 'Revenue',
        type: 'bar',
        data: revenueData,
        itemStyle: {
          color: '#34D399' // Green color for revenue
        }
      },
      {
        name: 'Expenses',
        type: 'bar',
        data: expensesData,
        itemStyle: {
          color: '#F87171' // Red color for expenses
        }
      }
    ]
  };

  if (!EChartsComponent) {
    return <div className="h-[500px] flex items-center justify-center">Loading chart...</div>;
  }

  return (
    <div>
      <EChartsComponent option={option} style={{ height: '500px' }} />
      <div className="mt-4 text-sm text-gray-500 text-center">
        Monthly Revenue and Expenses Overview
      </div>
    </div>
  );
}