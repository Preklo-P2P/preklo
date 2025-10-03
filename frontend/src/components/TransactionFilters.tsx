import { Button } from "@/components/ui/button";

interface DateRange {
  start: Date | null;
  end: Date | null;
}

interface AmountRange {
  min: number | null;
  max: number | null;
}

interface TransactionFiltersProps {
  isOpen: boolean;
  dateRange: DateRange;
  amountRange: AmountRange;
  onDateRangeChange: (range: DateRange) => void;
  onAmountRangeChange: (range: AmountRange) => void;
  onClearFilters: () => void;
}

export function TransactionFilters({
  isOpen,
  dateRange,
  amountRange,
  onDateRangeChange,
  onAmountRangeChange,
  onClearFilters,
}: TransactionFiltersProps) {
  if (!isOpen) return null;

  return (
    <div className="px-4 py-4 bg-muted/30 border-b border-border">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-foreground">Advanced Filters</h3>
          <Button variant="ghost" size="sm" onClick={onClearFilters}>
            Clear All
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Date Range */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-2">Date Range</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={dateRange.start ? dateRange.start.toISOString().split('T')[0] : ''}
                onChange={(e) => onDateRangeChange({ 
                  ...dateRange, 
                  start: e.target.value ? new Date(e.target.value) : null 
                })}
                className="flex-1 p-2 border border-border rounded-lg bg-background text-foreground text-sm"
              />
              <input
                type="date"
                value={dateRange.end ? dateRange.end.toISOString().split('T')[0] : ''}
                onChange={(e) => onDateRangeChange({ 
                  ...dateRange, 
                  end: e.target.value ? new Date(e.target.value) : null 
                })}
                className="flex-1 p-2 border border-border rounded-lg bg-background text-foreground text-sm"
              />
            </div>
          </div>

          {/* Amount Range */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-2">Amount Range</label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="Min"
                value={amountRange.min || ''}
                onChange={(e) => onAmountRangeChange({ 
                  ...amountRange, 
                  min: e.target.value ? parseFloat(e.target.value) : null 
                })}
                className="flex-1 p-2 border border-border rounded-lg bg-background text-foreground text-sm"
              />
              <input
                type="number"
                placeholder="Max"
                value={amountRange.max || ''}
                onChange={(e) => onAmountRangeChange({ 
                  ...amountRange, 
                  max: e.target.value ? parseFloat(e.target.value) : null 
                })}
                className="flex-1 p-2 border border-border rounded-lg bg-background text-foreground text-sm"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
