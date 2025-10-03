import { useState } from "react";
import { ArrowLeft, Search, HelpCircle, MessageCircle, BookOpen, Play, Mail, Users, ChevronRight, Star, Clock, CheckCircle } from "lucide-react";
import { ActionButton } from "@/components/ui/ActionButton";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";

interface HelpAndSupportProps {
  onNavigate: (page: string) => void;
}

type HelpSection = "overview" | "faq" | "guide" | "tutorials" | "contact" | "tickets" | "chat" | "forum";

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
  helpful: number;
  tags: string[];
}

interface SupportTicket {
  id: string;
  subject: string;
  status: "open" | "in-progress" | "resolved" | "closed";
  priority: "low" | "medium" | "high" | "urgent";
  createdAt: Date;
  updatedAt: Date;
  category: string;
}

const mockFAQs: FAQItem[] = [
  {
    id: "1",
    question: "How do I send money to another user?",
    answer: "To send money, tap the 'Send Money' button on your dashboard, enter the recipient's username, specify the amount, add a description (optional), and confirm the transaction. The recipient will receive the money instantly.",
    category: "Sending Money",
    helpful: 45,
    tags: ["send", "money", "transfer"]
  },
  {
    id: "2",
    question: "What currencies does Preklo support?",
    answer: "Preklo currently supports USDC (USD Coin) and APT (Aptos) tokens. We're working on adding more cryptocurrencies in the future.",
    category: "Currencies",
    helpful: 32,
    tags: ["currency", "usdc", "apt", "crypto"]
  },
  {
    id: "3",
    question: "How do I receive money from someone?",
    answer: "To receive money, share your @username with the sender, or generate a QR code from the 'Receive Money' section. The sender can scan your QR code or enter your username to send you money.",
    category: "Receiving Money",
    helpful: 28,
    tags: ["receive", "qr", "username"]
  },
  {
    id: "4",
    question: "Are there any fees for transactions?",
    answer: "Preklo charges a small network fee for blockchain transactions (typically $0.01-$0.05). This fee goes to the blockchain network, not to Preklo. We don't charge additional service fees.",
    category: "Fees",
    helpful: 41,
    tags: ["fees", "cost", "network"]
  },
  {
    id: "5",
    question: "How do I view my transaction history?",
    answer: "You can view your complete transaction history by tapping 'Transaction History' on your dashboard. You can filter by date, amount, type, and search for specific transactions.",
    category: "Transaction History",
    helpful: 23,
    tags: ["history", "transactions", "filter"]
  }
];

const mockTickets: SupportTicket[] = [
  {
    id: "TKT-001",
    subject: "Unable to send money to @john_doe",
    status: "resolved",
    priority: "medium",
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
    updatedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    category: "Technical Issue"
  },
  {
    id: "TKT-002",
    subject: "Question about transaction fees",
    status: "open",
    priority: "low",
    createdAt: new Date(Date.now() - 1 * 60 * 60 * 1000),
    updatedAt: new Date(Date.now() - 1 * 60 * 60 * 1000),
    category: "General Inquiry"
  }
];

export function HelpAndSupport({ onNavigate }: HelpAndSupportProps) {
  const [currentSection, setCurrentSection] = useState<HelpSection>("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const { toast } = useToast();

  const helpSections = [
    {
      id: "faq" as const,
      title: "Frequently Asked Questions",
      description: "Find quick answers to common questions",
      icon: HelpCircle,
      color: "text-blue-600",
      bgColor: "bg-blue-50"
    },
    {
      id: "guide" as const,
      title: "User Guide",
      description: "Step-by-step instructions for all features",
      icon: BookOpen,
      color: "text-green-600",
      bgColor: "bg-green-50"
    },
    {
      id: "tutorials" as const,
      title: "Video Tutorials",
      description: "Watch videos to learn how to use Preklo",
      icon: Play,
      color: "text-purple-600",
      bgColor: "bg-purple-50"
    },
    {
      id: "contact" as const,
      title: "Contact Support",
      description: "Get help from our support team",
      icon: Mail,
      color: "text-orange-600",
      bgColor: "bg-orange-50"
    },
    {
      id: "tickets" as const,
      title: "Support Tickets",
      description: "Track your support requests",
      icon: MessageCircle,
      color: "text-red-600",
      bgColor: "bg-red-50"
    },
    {
      id: "chat" as const,
      title: "Live Chat",
      description: "Chat with support in real-time",
      icon: MessageCircle,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50"
    },
    {
      id: "forum" as const,
      title: "Community Forum",
      description: "Connect with other Preklo users",
      icon: Users,
      color: "text-teal-600",
      bgColor: "bg-teal-50"
    }
  ];

  const categories = ["all", "Sending Money", "Receiving Money", "Currencies", "Fees", "Transaction History", "Technical Issue", "General Inquiry"];

  const filteredFAQs = mockFAQs.filter(faq => {
    const matchesSearch = searchQuery === "" || 
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesCategory = selectedCategory === "all" || faq.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "open":
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Open</Badge>;
      case "in-progress":
        return <Badge variant="default" className="bg-blue-100 text-blue-800">In Progress</Badge>;
      case "resolved":
        return <Badge variant="default" className="bg-green-100 text-green-800">Resolved</Badge>;
      case "closed":
        return <Badge variant="destructive" className="bg-gray-100 text-gray-800">Closed</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "urgent":
        return <Badge variant="destructive" className="bg-red-100 text-red-800">Urgent</Badge>;
      case "high":
        return <Badge variant="destructive" className="bg-orange-100 text-orange-800">High</Badge>;
      case "medium":
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Medium</Badge>;
      case "low":
        return <Badge variant="outline" className="bg-gray-100 text-gray-800">Low</Badge>;
      default:
        return <Badge variant="secondary">{priority}</Badge>;
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="text-center py-8">
        <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <HelpCircle className="h-10 w-10 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">How can we help you?</h2>
        <p className="text-muted-foreground">Get support, learn how to use Preklo, and connect with our community</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {helpSections.map((section) => {
          const Icon = section.icon;
          return (
            <Card 
              key={section.id} 
              className="cursor-pointer hover:shadow-md transition-shadow duration-200"
              onClick={() => setCurrentSection(section.id)}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 ${section.bgColor} rounded-lg flex items-center justify-center`}>
                    <Icon className={`h-6 w-6 ${section.color}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground mb-1">{section.title}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{section.description}</p>
                    <div className="flex items-center text-sm text-primary">
                      <span>Learn more</span>
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );

  const renderFAQ = () => (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search FAQs..."
            className="w-full pl-10 pr-4 py-3 border border-border rounded-xl bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-3 border border-border rounded-xl bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          {categories.map(category => (
            <option key={category} value={category}>
              {category === "all" ? "All Categories" : category}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-4">
        {filteredFAQs.map((faq) => (
          <Card key={faq.id}>
            <CardContent className="p-6">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <h3 className="font-semibold text-foreground">{faq.question}</h3>
                  <Badge variant="outline" className="text-xs">{faq.category}</Badge>
                </div>
                <p className="text-muted-foreground">{faq.answer}</p>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {faq.tags.map((tag, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Star className="h-4 w-4" />
                    <span>{faq.helpful} found helpful</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredFAQs.length === 0 && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Search className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-foreground mb-2">No FAQs found</h3>
          <p className="text-muted-foreground">Try adjusting your search terms or category filter</p>
        </div>
      )}
    </div>
  );

  const renderTickets = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-foreground">Support Tickets</h2>
        <ActionButton onClick={() => setCurrentSection("contact")}>
          Create New Ticket
        </ActionButton>
      </div>

      <div className="space-y-4">
        {mockTickets.map((ticket) => (
          <Card key={ticket.id}>
            <CardContent className="p-6">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-foreground mb-1">{ticket.subject}</h3>
                    <p className="text-sm text-muted-foreground">Ticket #{ticket.id}</p>
                  </div>
                  <div className="flex gap-2">
                    {getStatusBadge(ticket.status)}
                    {getPriorityBadge(ticket.priority)}
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span>Category: {ticket.category}</span>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      <span>Created {ticket.createdAt.toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" />
                      <span>Updated {ticket.updatedAt.toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderContact = () => (
    <div className="space-y-6">
      <div className="text-center py-8">
        <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <Mail className="h-10 w-10 text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground mb-2">Contact Support</h2>
        <p className="text-muted-foreground">We're here to help! Choose how you'd like to get in touch</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="cursor-pointer hover:shadow-md transition-shadow duration-200">
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <MessageCircle className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="font-semibold text-foreground mb-2">Live Chat</h3>
            <p className="text-sm text-muted-foreground mb-4">Chat with our support team in real-time</p>
            <Badge variant="default" className="bg-green-100 text-green-800">Available Now</Badge>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow duration-200">
          <CardContent className="p-6 text-center">
            <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="h-8 w-8 text-blue-600" />
            </div>
            <h3 className="font-semibold text-foreground mb-2">Email Support</h3>
            <p className="text-sm text-muted-foreground mb-4">Send us an email and we'll respond within 24 hours</p>
            <Badge variant="secondary">support@preklo.com</Badge>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create Support Ticket</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Subject</label>
            <input
              type="text"
              placeholder="Brief description of your issue"
              className="w-full p-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Category</label>
            <select className="w-full p-3 border border-border rounded-lg bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent">
              <option>Technical Issue</option>
              <option>Account Problem</option>
              <option>Transaction Issue</option>
              <option>Feature Request</option>
              <option>General Inquiry</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Description</label>
            <textarea
              placeholder="Please provide detailed information about your issue..."
              rows={4}
              className="w-full p-3 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
            />
          </div>
          <ActionButton 
            onClick={() => {
              toast({
                title: "Ticket created!",
                description: "We've received your support request and will respond soon.",
              });
            }}
            fullWidth
          >
            Submit Ticket
          </ActionButton>
        </CardContent>
      </Card>
    </div>
  );

  const renderSection = () => {
    switch (currentSection) {
      case "overview":
        return renderOverview();
      case "faq":
        return renderFAQ();
      case "tickets":
        return renderTickets();
      case "contact":
        return renderContact();
      default:
        return (
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold text-foreground mb-2">Coming Soon</h2>
            <p className="text-muted-foreground">This section is under development</p>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => onNavigate("dashboard")}
            className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-semibold text-foreground">Help & Support</h1>
            <p className="text-sm text-muted-foreground">
              {currentSection === "overview" ? "Get help and support" : 
               currentSection === "faq" ? "Frequently Asked Questions" :
               currentSection === "tickets" ? "Support Tickets" :
               currentSection === "contact" ? "Contact Support" :
               "Help & Support"}
            </p>
          </div>
          {currentSection !== "overview" && (
            <button
              onClick={() => setCurrentSection("overview")}
              className="p-2 rounded-full hover:bg-muted transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="Back to overview"
            >
              <HelpCircle className="h-5 w-5" />
            </button>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="px-4 py-6">
        {renderSection()}
      </main>
    </div>
  );
}
