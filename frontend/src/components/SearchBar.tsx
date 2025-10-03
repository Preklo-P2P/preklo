import { useState, useEffect } from "react";
import { Search, X, History } from "lucide-react";
import { Input } from "@/components/ui/input";

interface SearchResult {
  id: string;
  type: "user" | "transaction";
  username?: string;
  name?: string;
  description?: string;
  amount?: number;
}

interface SearchBarProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (page: string) => void;
}

export function SearchBar({ isOpen, onClose, onNavigate }: SearchBarProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Mock search results
    const mockResults: SearchResult[] = [
      { id: "1", type: "user", username: "@john_doe", name: "John Doe" },
      { id: "2", type: "user", username: "@maria_garcia", name: "Maria Garcia" },
      { id: "3", type: "transaction", transactionId: "tx_123", description: "Lunch payment", amount: 50.00 },
    ].filter(item => 
      item.username?.toLowerCase().includes(query.toLowerCase()) ||
      item.name?.toLowerCase().includes(query.toLowerCase()) ||
      item.description?.toLowerCase().includes(query.toLowerCase())
    );
    
    setSearchResults(mockResults);
    setIsSearching(false);
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      handleSearch(searchQuery);
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleResultClick = (result: SearchResult) => {
    if (result.type === "user") {
      onNavigate("send");
    } else if (result.type === "transaction") {
      onNavigate("history");
    }
    onClose();
  };

  const handleClose = () => {
    setSearchQuery("");
    setSearchResults([]);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="mt-4 relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search users, transactions..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 pr-10"
          autoFocus
        />
        <button
          onClick={handleClose}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded hover:bg-muted transition-colors duration-200"
          aria-label="Close search"
        >
          <X className="h-4 w-4 text-muted-foreground" />
        </button>
      </div>

      {/* Search Results */}
      {searchQuery.length >= 2 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-background border border-border rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
          {isSearching ? (
            <div className="p-4 text-center text-muted-foreground">
              <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              Searching...
            </div>
          ) : searchResults.length > 0 ? (
            <div className="p-2">
              {searchResults.map((result) => (
                <button
                  key={result.id}
                  className="w-full p-3 text-left hover:bg-muted rounded-lg transition-colors duration-200"
                  onClick={() => handleResultClick(result)}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                      {result.type === "user" ? (
                        <span className="text-sm font-bold text-primary">
                          {result.name?.charAt(0) || result.username?.charAt(1)}
                        </span>
                      ) : (
                        <History className="h-4 w-4 text-primary" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-foreground">
                        {result.type === "user" ? result.name : result.description}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {result.type === "user" ? result.username : `$${result.amount}`}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-4 text-center text-muted-foreground">
              No results found for "{searchQuery}"
            </div>
          )}
        </div>
      )}
    </div>
  );
}
