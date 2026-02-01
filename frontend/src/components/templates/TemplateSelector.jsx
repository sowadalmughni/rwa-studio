/**
 * Template Selector Component for RWA-Studio
 *
 * Allows users to preview and select asset page templates
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Check,
  Crown,
  Eye,
  Building,
  Briefcase,
  Landmark,
  Palette,
  TrendingUp,
} from "lucide-react";

// Template icons mapping
const TEMPLATE_ICONS = {
  "real-estate": Building,
  "private-equity": Briefcase,
  "debt-instrument": Landmark,
  "art-collectibles": Palette,
  "revenue-share": TrendingUp,
  default: Building,
  minimal: Building,
};

// Template preview images (placeholder gradients)
const TEMPLATE_PREVIEWS = {
  "real-estate": "linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%)",
  "private-equity": "linear-gradient(135deg, #0f172a 0%, #6366f1 100%)",
  "debt-instrument": "linear-gradient(135deg, #065f46 0%, #10b981 100%)",
  "art-collectibles": "linear-gradient(135deg, #7c2d12 0%, #ea580c 100%)",
  "revenue-share": "linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)",
  default: "linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)",
  minimal: "linear-gradient(135deg, #374151 0%, #6b7280 100%)",
};

export function TemplateSelector({ selectedTemplate, onSelectTemplate, assetType }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [previewTemplate, setPreviewTemplate] = useState(null);

  useEffect(() => {
    loadTemplates();
  }, [assetType]);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      // In production, fetch from API
      // const response = await fetch(`/api/assets/templates?asset_type=${assetType}`);
      // const data = await response.json();

      // For now, use mock data
      const mockTemplates = [
        {
          name: "real-estate",
          display_name: "Real Estate Fund",
          description: "Professional template optimized for real estate investments",
          asset_type: "real-estate",
          primary_color: "#1e3a5f",
          is_premium: false,
        },
        {
          name: "private-equity",
          display_name: "Private Equity",
          description: "Sophisticated template for PE fund shares",
          asset_type: "private-equity",
          primary_color: "#0f172a",
          is_premium: false,
        },
        {
          name: "debt-instrument",
          display_name: "Debt Instrument",
          description: "Clean template for bonds and loans",
          asset_type: "debt",
          primary_color: "#065f46",
          is_premium: false,
        },
        {
          name: "art-collectibles",
          display_name: "Art & Collectibles",
          description: "Visual-first template with provenance tracking",
          asset_type: "art",
          primary_color: "#7c2d12",
          is_premium: true,
        },
        {
          name: "revenue-share",
          display_name: "Revenue Share",
          description: "Dynamic template for royalties and revenue-sharing",
          asset_type: "revenue-share",
          primary_color: "#7c3aed",
          is_premium: false,
        },
        {
          name: "default",
          display_name: "Default",
          description: "Clean, professional template for any asset",
          asset_type: null,
          primary_color: "#3b82f6",
          is_premium: false,
        },
        {
          name: "minimal",
          display_name: "Minimal",
          description: "Simplified template with essential info",
          asset_type: null,
          primary_color: "#374151",
          is_premium: false,
        },
      ];

      // Filter by asset type if provided
      const filtered = assetType
        ? mockTemplates.filter((t) => t.asset_type === assetType || t.asset_type === null)
        : mockTemplates;

      setTemplates(filtered);
    } catch (error) {
      console.error("Failed to load templates:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (templateName) => {
    onSelectTemplate(templateName);
  };

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="animate-pulse">
            <div className="h-32 bg-gray-200 rounded-t-lg" />
            <CardContent className="p-4">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
              <div className="h-3 bg-gray-200 rounded w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Choose a Template</h3>
        <Badge variant="outline" className="text-xs">
          {templates.length} templates available
        </Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {templates.map((template) => {
          const Icon = TEMPLATE_ICONS[template.name] || Building;
          const isSelected = selectedTemplate === template.name;

          return (
            <Card
              key={template.name}
              className={`cursor-pointer transition-all hover:shadow-lg ${
                isSelected ? "ring-2 ring-primary" : ""
              }`}
              onClick={() => handleSelect(template.name)}
            >
              {/* Preview */}
              <div
                className="h-32 rounded-t-lg flex items-center justify-center relative"
                style={{ background: TEMPLATE_PREVIEWS[template.name] }}
              >
                <Icon className="h-12 w-12 text-white/80" />

                {/* Selected indicator */}
                {isSelected && (
                  <div className="absolute top-2 right-2 bg-white rounded-full p-1">
                    <Check className="h-4 w-4 text-primary" />
                  </div>
                )}

                {/* Premium badge */}
                {template.is_premium && (
                  <Badge className="absolute top-2 left-2 bg-yellow-500 hover:bg-yellow-600">
                    <Crown className="h-3 w-3 mr-1" />
                    Premium
                  </Badge>
                )}
              </div>

              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-semibold">{template.display_name}</h4>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      setPreviewTemplate(template);
                    }}
                  >
                    <Eye className="h-3 w-3" />
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground">{template.description}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Preview Modal would go here */}
    </div>
  );
}

export default TemplateSelector;
