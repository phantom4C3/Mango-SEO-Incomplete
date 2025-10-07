// frontend/components/settings/subscription-card.tsx

import React from 'react';
import { Button } from '../ui/button';
import { useUserStore } from '../../stores/use-user-store';

interface SubscriptionCardProps {
  planName: string;
  price: string;
  features: string[];
  isCurrentPlan: boolean;
  upgradeAction?: () => void;
  cancelAction?: () => void;
}

export const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  planName,
  price,
  features,
  isCurrentPlan,
  upgradeAction,
  cancelAction,
}) => {
  const { user } = useUserStore();

  return (
    <div className="bg-black border border-gray-800 rounded-xl p-6 flex flex-col gap-4 text-white shadow-md">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-yellow-500">{planName}</h3>
        <span className="text-gray-400">{price}</span>
      </div>
      <ul className="flex flex-col gap-2">
        {features.map((feature, index) => (
          <li key={index} className="text-gray-300 text-sm">
            • {feature}
          </li>
        ))}
      </ul>
      <div className="flex gap-4 mt-4">
        {!isCurrentPlan && (
          <Button
            className="bg-yellow-500 hover:bg-yellow-400 text-black font-semibold px-4 py-2"
            onClick={upgradeAction}
          >
            Upgrade
          </Button>
        )}
        {isCurrentPlan && cancelAction && (
          <Button
            className="bg-gray-800 hover:bg-gray-700 text-white font-semibold px-4 py-2"
            onClick={cancelAction}
          >
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
};
