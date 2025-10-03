import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Smartphone, Globe, Zap, Shield, Star, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface LandingPageProps {
  onNavigate: (page: string) => void;
}

export function LandingPage({ onNavigate }: LandingPageProps) {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  // Scroll to top when landing page loads
  useEffect(() => {
    // Always scroll to top when landing page loads
    window.scrollTo(0, 0);
    
    // Also handle hash navigation if present
    if (window.location.hash === '#top' || window.location.hash === '') {
      window.scrollTo(0, 0);
    }
  }, []);

  const handleGetStarted = () => {
    setIsLoading(true);
    // Simulate loading
    setTimeout(() => {
      setIsLoading(false);
      navigate("/register");
    }, 1000);
  };

  const handleSignIn = () => {
    navigate("/login");
  };

  const features = [
    {
      icon: <Smartphone className="h-8 w-8 text-primary" />,
      title: "Send Money Like a Text",
      description: "Send money globally using simple names like johnsmith - no complex account numbers or technical knowledge required."
    },
    {
      icon: <Globe className="h-8 w-8 text-primary" />,
      title: "Global Reach",
      description: "Send money anywhere in the world instantly with low fees and no geographic restrictions."
    },
    {
      icon: <Zap className="h-8 w-8 text-primary" />,
      title: "Lightning Fast",
      description: "Transactions complete in under 30 seconds instead of 3-5 days with traditional services."
    },
    {
      icon: <Shield className="h-8 w-8 text-primary" />,
      title: "Bank-Level Security",
      description: "Your money is protected with enterprise-grade security and advanced technology."
    }
  ];

  const stats = [
    { number: "1.7B", label: "Unbanked Adults" },
    { number: "$4.39T", label: "Global P2P Market" },
    { number: "1-2%", label: "Transaction Fees" },
    { number: "<30s", label: "Transaction Time" }
  ];

  const testimonials = [
    {
      name: "Sarah M.",
      location: "Nigeria",
      text: "Finally, a way to send money to my family abroad without the high fees and long wait times!",
      rating: 5
    },
    {
      name: "Carlos R.",
      location: "Philippines",
      text: "The name system is brilliant - no more copying long account numbers!",
      rating: 5
    },
    {
      name: "Aisha K.",
      location: "Kenya",
      text: "Preklo made global payments simple enough for my grandmother to use.",
      rating: 5
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-background border-b border-border px-4 py-4">
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div className="flex items-center gap-2">
            <img 
              src="/Preklo logo.png" 
              alt="Preklo" 
              className="h-8 w-auto"
            />
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" onClick={handleSignIn}>
              Sign In
            </Button>
            <Button onClick={handleGetStarted} disabled={isLoading}>
              {isLoading ? "Loading..." : "Get Started"}
              {!isLoading && <ArrowRight className="h-4 w-4 ml-2" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-4 py-12 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
            Send Money Globally
            <span className="block text-primary">Like a Text Message</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Send money anywhere using simple names like johnsmith - fast, secure, and affordable.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
            <Button 
              onClick={handleGetStarted} 
              size="lg" 
              disabled={isLoading}
              className="text-lg px-8 py-4"
            >
              {isLoading ? "Loading..." : "Start Sending Money"}
              {!isLoading && <ArrowRight className="h-5 w-5 ml-2" />}
            </Button>
            <Button variant="outline" size="lg" className="text-lg px-8 py-4">
              Watch Demo
            </Button>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-3xl mx-auto">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-primary mb-1">
                  {stat.number}
                </div>
                <div className="text-sm text-muted-foreground">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="px-4 py-16 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Why Choose Preklo?
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              We combine the best of traditional banking and modern technology to create 
              the most accessible payment platform ever built.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-6">
                <CardContent className="p-0">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                      {feature.icon}
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-foreground mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-muted-foreground">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            How It Works
          </h2>
          <p className="text-lg text-muted-foreground mb-12">
            Sending money with Preklo is as simple as sending a text message
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-foreground">1</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Choose Your Name
              </h3>
              <p className="text-muted-foreground">
                Register a unique name like johnsmith that others can use to send you money
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-foreground">2</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Send Money Instantly
              </h3>
              <p className="text-muted-foreground">
                Enter any name like johnsmith and amount to send money anywhere in the world
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary-foreground">3</span>
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Get Your Money
              </h3>
              <p className="text-muted-foreground">
                Receive instant notifications when money arrives and see all your transactions
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="px-4 py-16 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Loved by Users Worldwide
            </h2>
            <p className="text-lg text-muted-foreground">
              Join thousands of users who are already sending money the Preklo way
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="p-6">
                <CardContent className="p-0">
                  <div className="flex items-center gap-1 mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-muted-foreground mb-4 italic">
                    "{testimonial.text}"
                  </p>
                  <div>
                    <div className="font-semibold text-foreground">
                      {testimonial.name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {testimonial.location}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Ready to Revolutionize Your Payments?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            Join the future of global payments. Start sending money the Preklo way today.
          </p>
          <Button 
            onClick={handleGetStarted} 
            size="lg" 
            disabled={isLoading}
            className="text-lg px-8 py-4"
          >
            {isLoading ? "Loading..." : "Get Started Free"}
            {!isLoading && <ArrowRight className="h-5 w-5 ml-2" />}
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-muted/50 px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <img 
                src="/Preklo logo.png" 
                alt="Preklo" 
                className="h-6 w-auto"
              />
            </div>
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <button className="hover:text-foreground transition-colors">Privacy Policy</button>
              <button className="hover:text-foreground transition-colors">Terms of Service</button>
              <button className="hover:text-foreground transition-colors">Support</button>
            </div>
          </div>
          <div className="text-center text-sm text-muted-foreground mt-4">
            © 2025 Preklo
          </div>
        </div>
      </footer>
    </div>
  );
}
