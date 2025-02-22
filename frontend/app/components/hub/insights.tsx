import type { InsightData } from "~/api/transactions";
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from "@heroicons/react/24/solid";

interface InsightCardProps {
  title: string;
  items: Array<{
    name: string;
    amount: number;
    trend?: number;
  }>;
}

const InsightCard = ({ title, items }: InsightCardProps) => (
  <div className="bg-gray-900 rounded-lg p-4">
    <div className="flex justify-between items-center mb-4">
      <h3 className="text-lg font-semibold text-white">{title}</h3>
      <button className="text-gray-400 hover:text-white">
        <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z" />
        </svg>
      </button>
    </div>
    <div className="space-y-3">
      {items.map((item, index) => (
        <div key={index} className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-purple-500" />
            <span className="text-white">{item.name}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-white">${item.amount.toLocaleString()}</span>
            {item.trend && (
              <span className={`flex items-center ${item.trend > 0 ? 'text-red-500' : 'text-green-500'}`}>
                {item.trend > 0 ? (
                  <ArrowTrendingUpIcon className="w-4 h-4" />
                ) : (
                  <ArrowTrendingDownIcon className="w-4 h-4" />
                )}
                {Math.abs(item.trend)}%
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  </div>
);

interface InsightsProps {
  data: InsightData;
}

export default function Insights({ data }: InsightsProps) {
  const categoryItems = data.spending_by_category.map(item => ({
    name: item.category,
    amount: item.amount,
    trend: Math.floor(Math.random() * 100) - 50 // TODO: Replace with actual trend data
  }));

  const vendorItems = data.spending_by_entity.map(item => ({
    name: item.entity,
    amount: item.amount,
    trend: Math.floor(Math.random() * 100) - 50 // TODO: Replace with actual trend data
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <InsightCard title="Top Categories" items={categoryItems} />
      <InsightCard title="Top Vendors" items={vendorItems} />
    </div>
  );
} 