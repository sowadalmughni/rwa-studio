/**
 * Generate Asset Page Script for RWA-Studio
 * Author: Sowad Al-Mughni
 *
 * Generates shareable asset pages for RWA tokens with compliance badges
 */

const fs = require("fs");
const path = require("path");

// Template configurations
const Templates = {
  default: {
    name: "Default",
    description: "Clean, professional template suitable for most assets",
  },
  premium: {
    name: "Premium",
    description: "Enhanced template with additional sections and styling",
  },
  minimal: {
    name: "Minimal",
    description: "Simplified template with essential information only",
  },
};

async function generateAssetPage(taskArgs, hre) {
  console.log("Generating asset page with RWA-Studio...");

  const tokenAddress = taskArgs.token;
  const template = (taskArgs.template || "default").toLowerCase();

  console.log(`\nConfiguration:`);
  console.log(`   Token: ${tokenAddress}`);
  console.log(`   Template: ${template}`);

  if (!(template in Templates)) {
    throw new Error(
      `Invalid template: ${template}. Valid options: ${Object.keys(Templates).join(", ")}`
    );
  }

  try {
    // Get token contract
    const RWAToken = await hre.ethers.getContractFactory("RWAToken");
    const token = RWAToken.attach(tokenAddress);

    // Gather token information
    const tokenName = await token.name();
    const tokenSymbol = await token.symbol();
    const totalSupply = await token.totalSupply();
    const maxSupply = await token.maxSupply();
    const transfersEnabled = await token.transfersEnabled();
    const owner = await token.owner();
    const assetInfo = await token.assetInfo();

    console.log(`\nToken: ${tokenName} (${tokenSymbol})`);

    // Get compliance information
    const complianceAddress = await token.compliance();
    const identityRegistryAddress = await token.identityRegistry();

    let complianceRules = [];
    if (complianceAddress !== hre.ethers.ZeroAddress) {
      const ComplianceModule = await hre.ethers.getContractFactory("ComplianceModule");
      const compliance = ComplianceModule.attach(complianceAddress);

      const rules = await compliance.getRules();
      for (const ruleAddress of rules) {
        try {
          const rule = await hre.ethers.getContractAt("IComplianceRule", ruleAddress);
          const description = await rule.getRuleDescription();
          const isActive = await rule.isActive();
          if (isActive) {
            complianceRules.push(description);
          }
        } catch {
          // Skip rules that can't be queried
        }
      }
    }

    // Build page data
    const pageData = {
      token: {
        address: tokenAddress,
        name: tokenName,
        symbol: tokenSymbol,
        totalSupply: hre.ethers.formatEther(totalSupply),
        maxSupply: hre.ethers.formatEther(maxSupply),
        transfersEnabled: transfersEnabled,
        owner: owner,
      },
      asset: {
        type: assetInfo.assetType,
        framework: assetInfo.regulatoryFramework,
        jurisdiction: assetInfo.jurisdiction,
        description: assetInfo.description || `Tokenized ${assetInfo.assetType} asset`,
      },
      compliance: {
        hasModule: complianceAddress !== hre.ethers.ZeroAddress,
        hasIdentityRegistry: identityRegistryAddress !== hre.ethers.ZeroAddress,
        rules: complianceRules,
        badges: generateBadges(assetInfo.regulatoryFramework, complianceRules.length > 0),
      },
      network: hre.network.name,
      generatedAt: new Date().toISOString(),
    };

    // Generate HTML
    const html = generateHTML(pageData, template);

    // Save the page
    const pagesDir = path.join(__dirname, "..", "asset-pages");
    if (!fs.existsSync(pagesDir)) {
      fs.mkdirSync(pagesDir, { recursive: true });
    }

    const filename = `${tokenSymbol.toLowerCase()}-asset-page.html`;
    const filepath = path.join(pagesDir, filename);
    fs.writeFileSync(filepath, html);

    // Also generate a JSON data file
    const jsonFilename = `${tokenSymbol.toLowerCase()}-asset-data.json`;
    const jsonFilepath = path.join(pagesDir, jsonFilename);
    fs.writeFileSync(jsonFilepath, JSON.stringify(pageData, null, 2));

    // Generate shareable URLs (these would be real URLs in production)
    const baseUrl = "https://rwa-studio.com/assets";
    const pageUrl = `${baseUrl}/${tokenAddress}`;
    const shareUrl = `${pageUrl}?ref=share`;
    const badgeUrl = `${baseUrl}/badge/${tokenAddress}.svg`;

    console.log(`\nAsset page generated successfully!`);
    console.log(`\nFiles:`);
    console.log(`   HTML: ${filepath}`);
    console.log(`   Data: ${jsonFilepath}`);

    console.log(`\nURLs (for production deployment):`);
    console.log(`   Page: ${pageUrl}`);
    console.log(`   Share: ${shareUrl}`);
    console.log(`   Badge: ${badgeUrl}`);

    console.log(`\nEmbed Badge (copy to investor decks):`);
    console.log(
      `   <a href="${pageUrl}"><img src="${badgeUrl}" alt="Verified by RWA-Studio" /></a>`
    );

    return {
      success: true,
      url: pageUrl,
      shareUrl: shareUrl,
      badgeUrl: badgeUrl,
      filepath: filepath,
      data: pageData,
    };
  } catch (error) {
    console.error(`\nError generating asset page:`, error.message);
    throw error;
  }
}

function generateBadges(framework, hasCompliance) {
  const badges = [];

  // ERC-3643 badge
  badges.push({
    name: "ERC-3643 Compliant",
    icon: "[lock]",
    color: "#22c55e",
    description: "Token implements the ERC-3643 standard for compliant security tokens",
  });

  // Regulatory framework badge
  const frameworkBadges = {
    "reg-d": {
      name: "Regulation D",
      icon: "[doc]",
      color: "#3b82f6",
      description: "SEC Regulation D private placement",
    },
    "reg-s": {
      name: "Regulation S",
      icon: "[globe]",
      color: "#8b5cf6",
      description: "SEC Regulation S international offering",
    },
    "reg-cf": {
      name: "Regulation CF",
      icon: "[users]",
      color: "#f59e0b",
      description: "SEC Regulation Crowdfunding",
    },
    "reg-a": {
      name: "Regulation A+",
      icon: "[chart]",
      color: "#10b981",
      description: "SEC Regulation A+ mini-IPO",
    },
  };

  const fwKey = framework.toLowerCase().replace(" ", "-");
  if (fwKey in frameworkBadges) {
    badges.push(frameworkBadges[fwKey]);
  }

  // Compliance badge
  if (hasCompliance) {
    badges.push({
      name: "Active Compliance",
      icon: "[check]",
      color: "#06b6d4",
      description: "Token has active compliance rules enforcing transfer restrictions",
    });
  }

  // RWA-Studio verification
  badges.push({
    name: "RWA-Studio Verified",
    icon: "[shield]",
    color: "#6366f1",
    description: "Token created and verified by RWA-Studio",
  });

  return badges;
}

function generateHTML(data, _template) {
  const { token, asset, compliance, network, generatedAt } = data;

  // Generate badge HTML
  const badgeHTML = compliance.badges
    .map(
      (badge) => `
    <div class="badge" style="border-color: ${badge.color}">
      <span class="badge-icon">${badge.icon}</span>
      <span class="badge-name">${badge.name}</span>
    </div>
  `
    )
    .join("");

  // Generate compliance rules HTML
  const rulesHTML =
    compliance.rules.length > 0
      ? compliance.rules.map((rule) => `<li>${rule}</li>`).join("")
      : "<li>No specific transfer restrictions configured</li>";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${token.name} (${token.symbol}) - RWA-Studio</title>
  <meta name="description" content="${asset.description}">
  
  <!-- Open Graph / Social Media -->
  <meta property="og:type" content="website">
  <meta property="og:title" content="${token.name} - Tokenized ${asset.type}">
  <meta property="og:description" content="${asset.description}">
  <meta property="og:image" content="https://rwa-studio.com/og/${token.address}.png">
  
  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="${token.name} - Tokenized ${asset.type}">
  <meta name="twitter:description" content="${asset.description}">
  
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); min-height: 100vh; }
    .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
    
    header { text-align: center; padding: 2rem 0; }
    .logo { font-size: 1.5rem; font-weight: bold; color: #3b82f6; margin-bottom: 0.5rem; }
    .tagline { color: #6b7280; font-size: 0.875rem; }
    
    .hero { background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .hero h1 { font-size: 2rem; color: #111827; margin-bottom: 0.5rem; }
    .hero .symbol { color: #3b82f6; font-weight: 600; }
    .hero .description { color: #4b5563; margin: 1rem 0; }
    
    .badges { display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 1.5rem 0; }
    .badge { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; border-radius: 9999px; border: 2px solid; background: white; font-size: 0.875rem; font-weight: 500; }
    .badge-icon { font-size: 1rem; }
    
    .section { background: white; border-radius: 1rem; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .section h2 { font-size: 1.25rem; color: #111827; margin-bottom: 1rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }
    
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
    .info-item { padding: 1rem; background: #f9fafb; border-radius: 0.5rem; }
    .info-label { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.05em; }
    .info-value { font-size: 1.125rem; font-weight: 600; color: #111827; margin-top: 0.25rem; }
    .info-value.address { font-family: monospace; font-size: 0.75rem; word-break: break-all; }
    
    .rules-list { list-style: none; }
    .rules-list li { padding: 0.75rem 1rem; background: #f0fdf4; border-left: 4px solid #22c55e; margin-bottom: 0.5rem; border-radius: 0 0.5rem 0.5rem 0; }
    
    footer { text-align: center; padding: 2rem; color: #6b7280; font-size: 0.875rem; }
    footer a { color: #3b82f6; text-decoration: none; }
    footer a:hover { text-decoration: underline; }
    
    .cta-button { display: inline-block; padding: 0.75rem 2rem; background: #3b82f6; color: white; border-radius: 0.5rem; text-decoration: none; font-weight: 600; margin-top: 1rem; transition: background 0.2s; }
    .cta-button:hover { background: #2563eb; }
    
    .powered-by { display: inline-flex; align-items: center; gap: 0.5rem; margin-top: 2rem; padding: 0.5rem 1rem; background: #f3f4f6; border-radius: 0.5rem; font-size: 0.875rem; color: #4b5563; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo">🏛️ RWA-Studio</div>
      <div class="tagline">Tokenize Real-World Assets in 5 Clicks</div>
    </header>
    
    <main>
      <div class="hero">
        <h1>${token.name} <span class="symbol">(${token.symbol})</span></h1>
        <p class="description">${asset.description}</p>
        
        <div class="badges">
          ${badgeHTML}
        </div>
      </div>
      
      <div class="section">
        <h2>📊 Token Details</h2>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">Asset Type</div>
            <div class="info-value">${asset.type.replace("-", " ").replace(/\b\w/g, (l) => l.toUpperCase())}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Regulatory Framework</div>
            <div class="info-value">${asset.framework.toUpperCase().replace("-", " ")}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Jurisdiction</div>
            <div class="info-value">${asset.jurisdiction}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Network</div>
            <div class="info-value">${network.charAt(0).toUpperCase() + network.slice(1)}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Total Supply</div>
            <div class="info-value">${parseFloat(token.totalSupply).toLocaleString()}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Max Supply</div>
            <div class="info-value">${parseFloat(token.maxSupply).toLocaleString()}</div>
          </div>
        </div>
        
        <div class="info-item" style="margin-top: 1rem;">
          <div class="info-label">Contract Address</div>
          <div class="info-value address">${token.address}</div>
        </div>
      </div>
      
      <div class="section">
        <h2>🔒 Compliance Rules</h2>
        <p style="color: #4b5563; margin-bottom: 1rem;">This token enforces the following transfer restrictions:</p>
        <ul class="rules-list">
          ${rulesHTML}
        </ul>
      </div>
      
      <div class="section" style="text-align: center;">
        <h2>🚀 Interested in This Offering?</h2>
        <p style="color: #4b5563;">Contact the issuer for more information about participating in this tokenized asset offering.</p>
        <a href="mailto:issuer@example.com" class="cta-button">Contact Issuer</a>
        
        <div class="powered-by">
          🔒 Reg-compliant token generated by <a href="https://rwa-studio.com">RWA-Studio</a>
        </div>
      </div>
    </main>
    
    <footer>
      <p>Generated on ${new Date(generatedAt).toLocaleDateString()} • Token verified by <a href="https://rwa-studio.com">RWA-Studio</a></p>
      <p style="margin-top: 0.5rem;">⚠️ This is an informational page. Always conduct your own due diligence before investing.</p>
    </footer>
  </div>
</body>
</html>`;
}

module.exports = { generateAssetPage };
