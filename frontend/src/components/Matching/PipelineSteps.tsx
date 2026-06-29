import { Check } from "lucide-react";
import type { PipelineStep } from "../../types/matching";

interface PipelineStepsProps {
  steps: PipelineStep[];
}

export default function PipelineSteps({ steps }: PipelineStepsProps) {
  return (
    <div className="flex items-center justify-center gap-0 py-6">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          {/* Step indicator */}
          <div className="flex flex-col items-center gap-2">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-medium transition-all duration-300 ${
                step.status === "completed"
                  ? "bg-green-500 text-white"
                  : step.status === "active"
                  ? "bg-blue-500 text-white animate-pulse shadow-[0_0_0_4px_rgba(59,130,246,0.3)]"
                  : "bg-gray-200 text-gray-400 dark:bg-gray-700 dark:text-gray-500"
              }`}
            >
              {step.status === "completed" ? (
                <Check className="h-5 w-5" />
              ) : (
                index + 1
              )}
            </div>
            <span
              className={`text-xs font-medium ${
                step.status === "completed"
                  ? "text-green-600 dark:text-green-400"
                  : step.status === "active"
                  ? "text-blue-600 dark:text-blue-400"
                  : "text-gray-400 dark:text-gray-500"
              }`}
            >
              {step.label}
            </span>
          </div>
          {/* Connector line (not after last step) */}
          {index < steps.length - 1 && (
            <div
              className={`mx-2 h-0.5 w-12 md:w-20 transition-colors duration-300 ${
                step.status === "completed"
                  ? "bg-green-500"
                  : steps[index + 1]?.status === "active" || steps[index + 1]?.status === "completed"
                  ? "bg-green-500"
                  : "bg-gray-300 dark:bg-gray-600"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}
