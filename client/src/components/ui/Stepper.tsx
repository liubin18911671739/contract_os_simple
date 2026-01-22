interface StepperProps {
  steps: Array<{ label: string; status: 'pending' | 'active' | 'completed' | 'error' }>;
}

export function Stepper({ steps }: StepperProps) {
  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => (
        <div key={index} className="flex-1 flex items-center">
          <div className="flex flex-col items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step.status === 'completed'
                  ? 'bg-green-500 text-white'
                  : step.status === 'active'
                    ? 'bg-blue-500 text-white'
                    : step.status === 'error'
                      ? 'bg-red-500 text-white'
                      : 'bg-gray-200 text-gray-600'
              }`}
            >
              {step.status === 'completed' ? '✓' : index + 1}
            </div>
            <div className="mt-2 text-xs text-center text-gray-600">{step.label}</div>
          </div>
          {index < steps.length - 1 && (
            <div
              className={`flex-1 h-1 mx-2 ${
                step.status === 'completed' ? 'bg-green-500' : 'bg-gray-200'
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}
