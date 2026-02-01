/**
 * Share Widget Component for RWA-Studio
 * Phase 4: Growth Features
 * 
 * Social sharing buttons with copy embed code functionality
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from '@/components/ui/popover';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { 
  Share2, 
  Copy, 
  Check, 
  Twitter, 
  Linkedin, 
  Mail, 
  Link2,
  Code,
  MessageCircle
} from 'lucide-react';

export function ShareWidget({ tokenAddress, tokenName, tokenSymbol }) {
  const [copied, setCopied] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

  const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
  const pageUrl = `${baseUrl}/assets/${tokenAddress}`;
  const badgeUrl = `${baseUrl}/api/badge/${tokenAddress}.svg`;

  const shareUrls = {
    twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(pageUrl)}&text=${encodeURIComponent(`Check out ${tokenName} (${tokenSymbol}) - a tokenized asset on RWA-Studio 🔒`)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(pageUrl)}`,
    telegram: `https://t.me/share/url?url=${encodeURIComponent(pageUrl)}&text=${encodeURIComponent(`Check out ${tokenName} on RWA-Studio`)}`,
    email: `mailto:?subject=${encodeURIComponent(`${tokenName} - Investment Opportunity`)}&body=${encodeURIComponent(`Check out this tokenized asset: ${pageUrl}`)}`
  };

  const embedCodes = {
    html: `<a href="${pageUrl}" target="_blank"><img src="${badgeUrl}" alt="${tokenName} - Verified by RWA-Studio" /></a>`,
    markdown: `[![${tokenName} - Verified by RWA-Studio](${badgeUrl})](${pageUrl})`,
    iframe: `<iframe src="${pageUrl}?embed=true" width="100%" height="400" frameborder="0"></iframe>`
  };

  const copyToClipboard = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleShare = (platform) => {
    window.open(shareUrls[platform], '_blank', 'width=600,height=400');
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Share2 className="h-4 w-4" />
          Share
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">Share {tokenSymbol}</h4>
            <Badge variant="outline" className="text-xs">
              🔒 ERC-3643
            </Badge>
          </div>

          <Tabs defaultValue="social" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="social">Social</TabsTrigger>
              <TabsTrigger value="embed">Embed</TabsTrigger>
            </TabsList>

            <TabsContent value="social" className="space-y-3 pt-3">
              {/* Social Share Buttons */}
              <div className="grid grid-cols-4 gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex-col h-auto py-3"
                  onClick={() => handleShare('twitter')}
                >
                  <Twitter className="h-5 w-5 mb-1 text-[#1DA1F2]" />
                  <span className="text-xs">Twitter</span>
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex-col h-auto py-3"
                  onClick={() => handleShare('linkedin')}
                >
                  <Linkedin className="h-5 w-5 mb-1 text-[#0A66C2]" />
                  <span className="text-xs">LinkedIn</span>
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex-col h-auto py-3"
                  onClick={() => handleShare('telegram')}
                >
                  <MessageCircle className="h-5 w-5 mb-1 text-[#0088cc]" />
                  <span className="text-xs">Telegram</span>
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex-col h-auto py-3"
                  onClick={() => handleShare('email')}
                >
                  <Mail className="h-5 w-5 mb-1 text-gray-600" />
                  <span className="text-xs">Email</span>
                </Button>
              </div>

              {/* Copy Link */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Direct Link</Label>
                <div className="flex gap-2">
                  <Input 
                    value={pageUrl} 
                    readOnly 
                    className="text-xs h-9"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="shrink-0"
                    onClick={() => copyToClipboard(pageUrl, 'link')}
                  >
                    {copied === 'link' ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="embed" className="space-y-3 pt-3">
              {/* Badge Preview */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Badge Preview</Label>
                <div className="flex items-center justify-center p-4 bg-gray-50 rounded-lg">
                  <img 
                    src={badgeUrl} 
                    alt={`${tokenName} badge`}
                    className="max-h-8"
                  />
                </div>
              </div>

              {/* HTML Embed */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">HTML</Label>
                <div className="flex gap-2">
                  <Input 
                    value={embedCodes.html} 
                    readOnly 
                    className="text-xs h-9 font-mono"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="shrink-0"
                    onClick={() => copyToClipboard(embedCodes.html, 'html')}
                  >
                    {copied === 'html' ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Code className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* Markdown Embed */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Markdown</Label>
                <div className="flex gap-2">
                  <Input 
                    value={embedCodes.markdown} 
                    readOnly 
                    className="text-xs h-9 font-mono"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="shrink-0"
                    onClick={() => copyToClipboard(embedCodes.markdown, 'markdown')}
                  >
                    {copied === 'markdown' ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* Badge URL */}
              <div className="space-y-2">
                <Label className="text-xs text-muted-foreground">Badge URL</Label>
                <div className="flex gap-2">
                  <Input 
                    value={badgeUrl} 
                    readOnly 
                    className="text-xs h-9"
                  />
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="shrink-0"
                    onClick={() => copyToClipboard(badgeUrl, 'badge')}
                  >
                    {copied === 'badge' ? (
                      <Check className="h-4 w-4 text-green-500" />
                    ) : (
                      <Link2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <p className="text-xs text-muted-foreground text-center">
            Sharing helps grow the RWA ecosystem 🌱
          </p>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default ShareWidget;
