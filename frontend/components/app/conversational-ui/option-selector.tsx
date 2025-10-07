/**
 * Option Selector Component
 * Provides interactive option selection in conversational UI
 * Displays buttons, menus, or choice lists for user interaction
 */

import React from 'react';
import { Button } from '@/components/custom-ui/extras/button';
import { Card, CardContent } from '@/components/custom-ui/extras/card';
import { ChevronRightIcon } from '@radix-ui/react-icons';
import { cn } from '../../../lib/utils'; 

export interface Option {
  id: string;
  label: string;
  value: string;
  description?: string;
  icon?: React.ReactNode;
  disabled?: boolean;
  action?: () => void;
}

export interface OptionSelectorProps {
  options: Option[];
  title?: string;
  description?: string;
  variant?: 'buttons' | 'cards' | 'list';
  columns?: number;
  onSelect: (option: Option) => void;
  className?: string;
  disabled?: boolean;
}

export const OptionSelector: React.FC<OptionSelectorProps> = ({
  options,
  title,
  description,
  variant = 'buttons',
  columns = 1,
  onSelect,
  className,
  disabled = false
}) => {
  const { isLoading } = useConversationStore();

  const handleOptionClick = (option: Option) => {
    if (!disabled && !option.disabled && !isLoading) {
      onSelect(option);
    }
  };

  const renderButtons = () => (
    <div className={cn(
      "flex flex-wrap gap-2",
      columns > 1 && "grid grid-cols-2 gap-3",
      columns > 2 && "md:grid-cols-3",
      columns > 3 && "lg:grid-cols-4"
    )}>
      {options.map((option) => (
        <Button
          key={option.id}
          variant="outline"
          className={cn(
            "min-w-[120px] justify-start text-left h-auto py-3 px-4",
            "transition-all duration-200 hover:scale-105",
            "bg-gradient-to-r from-[#ffb600] to-[#ff8c00] text-black", // Mango yellow to orange-yellow gradient
            "hover:from-[#ffcc00] hover:to-[#ff9900]", // Lighter gradient on hover
            option.disabled && "opacity-50 cursor-not-allowed",
            disabled && "opacity-50 cursor-not-allowed"
          )}
          onClick={() => handleOptionClick(option)}
          disabled={disabled || option.disabled || isLoading}
        >
          <div className="flex flex-col items-start gap-1">
            {option.icon && (
              <span className="mb-1 text-lg text-black">{option.icon}</span>
            )}
            <span className="font-medium text-black">{option.label}</span>
            {option.description && (
              <span className="text-xs text-gray-300 font-normal">
                {option.description}
              </span>
            )}
          </div>
        </Button>
      ))}
    </div>
  );

  const renderCards = () => (
    <div className={cn(
      "grid gap-4",
      columns === 1 && "grid-cols-1",
      columns === 2 && "grid-cols-1 md:grid-cols-2",
      columns === 3 && "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
      columns >= 4 && "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
    )}>
      {options.map((option) => (
        <Card
          key={option.id}
          className={cn(
            "cursor-pointer transition-all duration-200 hover:shadow-md hover:border-[#ffb600]/50 bg-[#1a1a1a]", // Dark black background
            "group hover:scale-[1.02]",
            (disabled || option.disabled) && "opacity-50 cursor-not-allowed",
            isLoading && "opacity-50 cursor-not-allowed"
          )}
          onClick={() => handleOptionClick(option)}
        >
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              {option.icon && (
                <div className="flex-shrink-0 mt-1 text-[#ffb600]">
                  {option.icon}
                </div>
              )}
              <div className="flex-1 space-y-2">
                <h3 className="font-medium leading-tight group-hover:text-[#ffb600]">
                  {option.label}
                </h3>
                {option.description && (
                  <p className="text-sm text-gray-400">
                    {option.description}
                  </p>
                )}
              </div>
              <ChevronRightIcon className="flex-shrink-0 w-4 h-4 mt-1 text-gray-400 group-hover:text-[#ffb600]" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  const renderList = () => (
    <div className="space-y-2">
      {options.map((option) => (
        <div
          key={option.id}
          className={cn(
            "flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 bg-[#1a1a1a]", // Dark black background
            "cursor-pointer hover:bg-[#2a2a2a] hover:border-[#ffb600]/50",
            "group hover:scale-[1.01]",
            (disabled || option.disabled) && "opacity-50 cursor-not-allowed",
            isLoading && "opacity-50 cursor-not-allowed"
          )}
          onClick={() => handleOptionClick(option)}
        >
          {option.icon && (
            <div className="flex-shrink-0 text-[#ffb600]">
              {option.icon}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate group-hover:text-[#ffb600]">
              {option.label}
            </p>
            {option.description && (
              <p className="text-sm text-gray-400 truncate">
                {option.description}
              </p>
            )}
          </div>
          <ChevronRightIcon className="flex-shrink-0 w-4 h-4 text-gray-400 group-hover:text-[#ffb600]" />
        </div>
      ))}
    </div>
  );

  return (
    <div className={cn("space-y-4 bg-[#000000]", className)}> {/* Dark black background */}
      {(title || description) && (
        <div className="space-y-2">
          {title && (
            <h3 className="text-lg font-medium text-[#ffb600]">
              {title}
            </h3>
          )}
          {description && (
            <p className="text-sm text-gray-300">
              {description}
            </p>
          )}
        </div>
      )}
      
      {variant === 'buttons' && renderButtons()}
      {variant === 'cards' && renderCards()}
      {variant === 'list' && renderList()}

      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#000000]/80 backdrop-blur-sm rounded-lg">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#ffb600]"></div>
        </div>
      )}
    </div>
  );
};

// Additional specialized option selectors

interface QuickReplyOptionsProps {
  options: string[];
  onSelect: (option: string) => void;
  maxOptions?: number;
  className?: string;
}

export const QuickReplyOptions: React.FC<QuickReplyOptionsProps> = ({
  options,
  onSelect,
  maxOptions = 4,
  className
}) => {
  const quickOptions = options.slice(0, maxOptions).map((option, index) => ({
    id: `quick-${index}`,
    label: option,
    value: option
  }));

  return (
    <OptionSelector
      options={quickOptions}
      variant="buttons"
      columns={Math.min(quickOptions.length, 4)}
      onSelect={(option) => onSelect(option.value)}
      className={className}
    />
  );
};

interface StyleOption {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  examples: string[];
}

interface StyleSelectorProps {
  styles: StyleOption[];
  onStyleSelect: (styleId: string) => void;
  selectedStyle?: string;
}

export const StyleSelector: React.FC<StyleSelectorProps> = ({
  styles,
  onStyleSelect,
  selectedStyle
}) => {
  const options: Option[] = styles.map(style => ({
    id: style.id,
    label: style.name,
    value: style.id,
    description: style.description,
    icon: style.icon,
    disabled: false
  }));

  return (
    <OptionSelector
      options={options}
      title="Choose Content Style"
      description="Select the format that best fits your content needs"
      variant="cards"
      columns={2}
      onSelect={(option) => onStyleSelect(option.value)}
      className="style-selector"
    />
  );
};

interface CMSOption {
  id: string;
  name: string;
  logo: React.ReactNode;
  description: string;
  status: 'connected' | 'disconnected' | 'pending';
}

interface CMSSelectorProps {
  platforms: CMSOption[];
  onPlatformSelect: (platformId: string) => void;
  onConnectRequest: (platformId: string) => void;
}

export const CMSSelector: React.FC<CMSSelectorProps> = ({
  platforms,
  onPlatformSelect,
  onConnectRequest
}) => {
  const options: Option[] = platforms.map(platform => ({
    id: platform.id,
    label: platform.name,
    value: platform.id,
    description: platform.description,
    icon: platform.logo,
    disabled: platform.status === 'disconnected',
    action: platform.status === 'disconnected' 
      ? () => onConnectRequest(platform.id)
      : () => onPlatformSelect(platform.id)
  }));

  return (
    <OptionSelector
      options={options}
      title="Select CMS Platform"
      description="Choose where to publish your content"
      variant="cards"
      columns={2}
      onSelect={(option) => option.action?.()}
      className="cms-selector"
    />
  );
};

// Hook for using option selector in conversational flow
export const useOptionSelector = () => {
  const { addMessage, setIsLoading } = useConversationStore();

  const showOptions = async (
    options: Option[],
    title?: string,
    description?: string,
    variant: OptionSelectorProps['variant'] = 'buttons'
  ): Promise<Option> => {
    return new Promise((resolve) => {
      // Create a unique ID for this option set
      const optionSetId = `options-${Date.now()}`;
      
      // Add message with options to conversation
      addMessage({
        id: optionSetId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        type: 'suggestion',
        metadata: {
          options,
          title,
          description,
          variant
        }
      });

      // Create event listener for option selection
      const handleOptionSelect = (event: CustomEvent<{ option: Option }>) => {
        if (event.detail.option) {
          resolve(event.detail.option);
          window.removeEventListener('optionSelected', handleOptionSelect as EventListener);
        }
      };

      window.addEventListener('optionSelected', handleOptionSelect as EventListener);
    });
  };

  return { showOptions };
};

export default OptionSelector;