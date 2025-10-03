import { Check } from "lucide-react";

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
  stepTitles: string[];
}

export function StepIndicator({ currentStep, totalSteps, stepTitles }: StepIndicatorProps) {
  return (
    <div className="px-4 py-2">
      <div className="flex gap-2">
        {Array.from({ length: totalSteps }, (_, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < currentStep;
          const isCurrent = stepNumber === currentStep;
          
          return (
            <div
              key={stepNumber}
              className={`flex-1 h-1 rounded-full transition-colors duration-300 relative ${
                isCompleted || isCurrent ? "bg-primary" : "bg-muted"
              }`}
            >
              {isCompleted && (
                <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-primary rounded-full flex items-center justify-center">
                  <Check className="h-2 w-2 text-primary-foreground" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
