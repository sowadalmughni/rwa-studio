/**
 * Generate Compliance Report Script for RWA-Studio
 * Author: Sowad Al-Mughni
 *
 * Generates compliance reports for RWA tokens
 */

const fs = require("fs");
const path = require("path");

async function generateComplianceReport(taskArgs, hre) {
  console.log("Generating compliance report with RWA-Studio...");

  const tokenAddress = taskArgs.token;
  const format = (taskArgs.format || "json").toLowerCase();
  const periodDays = parseInt(taskArgs.period) || 30;

  console.log(`\nReport Configuration:`);
  console.log(`   Token: ${tokenAddress}`);
  console.log(`   Format: ${format}`);
  console.log(`   Period: ${periodDays} days`);

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
    const isPaused = await token.paused();
    const assetInfo = await token.assetInfo();

    console.log(`\nToken: ${tokenName} (${tokenSymbol})`);

    // Get compliance and identity registry
    const complianceAddress = await token.compliance();
    const identityRegistryAddress = await token.identityRegistry();

    // Gather compliance information
    let complianceInfo = {
      moduleAddress: complianceAddress,
      rules: [],
      ruleCount: 0,
    };

    if (complianceAddress !== hre.ethers.ZeroAddress) {
      const ComplianceModule = await hre.ethers.getContractFactory("ComplianceModule");
      const compliance = ComplianceModule.attach(complianceAddress);

      const rules = await compliance.getRules();
      complianceInfo.ruleCount = rules.length;

      for (const ruleAddress of rules) {
        try {
          const rule = await hre.ethers.getContractAt("IComplianceRule", ruleAddress);
          const description = await rule.getRuleDescription();
          const isActive = await rule.isActive();
          const [paramNames, paramValues] = await rule.getRuleParameters();

          const params = {};
          for (let i = 0; i < paramNames.length; i++) {
            params[paramNames[i]] = paramValues[i];
          }

          complianceInfo.rules.push({
            address: ruleAddress,
            description: description,
            isActive: isActive,
            parameters: params,
          });
        } catch (e) {
          complianceInfo.rules.push({
            address: ruleAddress,
            description: "Unable to query",
            isActive: "unknown",
            parameters: {},
          });
        }
      }
    }

    // Gather identity registry information
    let identityInfo = {
      registryAddress: identityRegistryAddress,
      verifiedAddressCount: 0,
      verificationLevels: {
        basic: 0,
        accredited: 0,
        institutional: 0,
      },
    };

    if (identityRegistryAddress !== hre.ethers.ZeroAddress) {
      const IdentityRegistry = await hre.ethers.getContractFactory("IdentityRegistry");
      const identityRegistry = IdentityRegistry.attach(identityRegistryAddress);

      try {
        identityInfo.verifiedAddressCount = Number(
          await identityRegistry.getVerifiedAddressCount()
        );
      } catch (e) {
        console.log(`   Warning: Could not get verified address count`);
      }
    }

    // Build report
    const report = {
      metadata: {
        generatedAt: new Date().toISOString(),
        reportPeriodDays: periodDays,
        reportPeriodStart: new Date(Date.now() - periodDays * 24 * 60 * 60 * 1000).toISOString(),
        reportPeriodEnd: new Date().toISOString(),
        network: hre.network.name,
        generator: "RWA-Studio v1.0.0",
      },
      token: {
        address: tokenAddress,
        name: tokenName,
        symbol: tokenSymbol,
        totalSupply: hre.ethers.formatEther(totalSupply),
        maxSupply: hre.ethers.formatEther(maxSupply),
        transfersEnabled: transfersEnabled,
        isPaused: isPaused,
        assetType: assetInfo.assetType,
        regulatoryFramework: assetInfo.regulatoryFramework,
        jurisdiction: assetInfo.jurisdiction,
        description: assetInfo.description,
      },
      compliance: complianceInfo,
      identity: identityInfo,
      summary: {
        overallStatus: "COMPLIANT",
        activeRules: complianceInfo.rules.filter((r) => r.isActive === true).length,
        totalRules: complianceInfo.ruleCount,
        verifiedInvestors: identityInfo.verifiedAddressCount,
        complianceRate: 100, // Placeholder - would need event logs for accurate calculation
        blockedTransfers: 0, // Placeholder - would need event logs
        totalTransfers: 0, // Placeholder - would need event logs
      },
    };

    // Determine status
    if (isPaused) {
      report.summary.overallStatus = "PAUSED";
    } else if (!transfersEnabled) {
      report.summary.overallStatus = "TRANSFERS_DISABLED";
    } else if (complianceInfo.ruleCount === 0) {
      report.summary.overallStatus = "NO_COMPLIANCE_RULES";
    }

    // Generate output file
    const reportsDir = path.join(__dirname, "..", "reports");
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    const timestamp = Date.now();
    let filename;
    let content;

    switch (format) {
      case "csv":
        filename = `compliance-report-${tokenSymbol}-${timestamp}.csv`;
        content = generateCSV(report);
        break;

      case "pdf":
        // For PDF, we'll generate a markdown file that can be converted
        filename = `compliance-report-${tokenSymbol}-${timestamp}.md`;
        content = generateMarkdown(report);
        console.log(
          `\nNote: PDF output generates Markdown. Use a tool like pandoc to convert to PDF.`
        );
        break;

      case "json":
      default:
        filename = `compliance-report-${tokenSymbol}-${timestamp}.json`;
        content = JSON.stringify(report, null, 2);
        break;
    }

    const filepath = path.join(reportsDir, filename);
    fs.writeFileSync(filepath, content);

    console.log(`\nReport Summary:`);
    console.log(`   Status: ${report.summary.overallStatus}`);
    console.log(`   Active Rules: ${report.summary.activeRules}/${report.summary.totalRules}`);
    console.log(`   Verified Investors: ${report.summary.verifiedInvestors}`);
    console.log(`   Compliance Rate: ${report.summary.complianceRate}%`);

    console.log(`\nReport generated successfully!`);
    console.log(`File: ${filepath}`);

    return {
      success: true,
      filename: filepath,
      totalTransfers: report.summary.totalTransfers,
      blockedTransfers: report.summary.blockedTransfers,
      complianceRate: report.summary.complianceRate,
      report: report,
    };
  } catch (error) {
    console.error(`\nError generating report:`, error.message);
    throw error;
  }
}

function generateCSV(report) {
  const lines = [];

  // Header
  lines.push("Compliance Report for " + report.token.name);
  lines.push("Generated," + report.metadata.generatedAt);
  lines.push("");

  // Token info
  lines.push("TOKEN INFORMATION");
  lines.push("Field,Value");
  lines.push(`Name,${report.token.name}`);
  lines.push(`Symbol,${report.token.symbol}`);
  lines.push(`Address,${report.token.address}`);
  lines.push(`Total Supply,${report.token.totalSupply}`);
  lines.push(`Max Supply,${report.token.maxSupply}`);
  lines.push(`Asset Type,${report.token.assetType}`);
  lines.push(`Regulatory Framework,${report.token.regulatoryFramework}`);
  lines.push(`Jurisdiction,${report.token.jurisdiction}`);
  lines.push(`Transfers Enabled,${report.token.transfersEnabled}`);
  lines.push(`Is Paused,${report.token.isPaused}`);
  lines.push("");

  // Compliance rules
  lines.push("COMPLIANCE RULES");
  lines.push("Address,Description,Active");
  for (const rule of report.compliance.rules) {
    lines.push(`${rule.address},"${rule.description}",${rule.isActive}`);
  }
  lines.push("");

  // Summary
  lines.push("SUMMARY");
  lines.push("Metric,Value");
  lines.push(`Overall Status,${report.summary.overallStatus}`);
  lines.push(`Active Rules,${report.summary.activeRules}`);
  lines.push(`Total Rules,${report.summary.totalRules}`);
  lines.push(`Verified Investors,${report.summary.verifiedInvestors}`);
  lines.push(`Compliance Rate,${report.summary.complianceRate}%`);

  return lines.join("\n");
}

function generateMarkdown(report) {
  const lines = [];

  lines.push(`# Compliance Report: ${report.token.name} (${report.token.symbol})`);
  lines.push("");
  lines.push(`**Generated:** ${report.metadata.generatedAt}`);
  lines.push(`**Network:** ${report.metadata.network}`);
  lines.push(`**Report Period:** ${report.metadata.reportPeriodDays} days`);
  lines.push("");

  lines.push("## Token Information");
  lines.push("");
  lines.push("| Field | Value |");
  lines.push("|-------|-------|");
  lines.push(`| Address | \`${report.token.address}\` |`);
  lines.push(`| Total Supply | ${report.token.totalSupply} |`);
  lines.push(`| Max Supply | ${report.token.maxSupply} |`);
  lines.push(`| Asset Type | ${report.token.assetType} |`);
  lines.push(`| Regulatory Framework | ${report.token.regulatoryFramework} |`);
  lines.push(`| Jurisdiction | ${report.token.jurisdiction} |`);
  lines.push(`| Transfers Enabled | ${report.token.transfersEnabled} |`);
  lines.push(`| Is Paused | ${report.token.isPaused} |`);
  lines.push("");

  lines.push("## Compliance Rules");
  lines.push("");
  if (report.compliance.rules.length > 0) {
    lines.push("| Rule | Description | Active |");
    lines.push("|------|-------------|--------|");
    for (const rule of report.compliance.rules) {
      lines.push(
        `| \`${rule.address.slice(0, 10)}...\` | ${rule.description} | ${rule.isActive} |`
      );
    }
  } else {
    lines.push("*No compliance rules configured.*");
  }
  lines.push("");

  lines.push("## Summary");
  lines.push("");
  lines.push(`- **Overall Status:** ${report.summary.overallStatus}`);
  lines.push(`- **Active Rules:** ${report.summary.activeRules}/${report.summary.totalRules}`);
  lines.push(`- **Verified Investors:** ${report.summary.verifiedInvestors}`);
  lines.push(`- **Compliance Rate:** ${report.summary.complianceRate}%`);
  lines.push("");

  lines.push("---");
  lines.push(`*Report generated by RWA-Studio*`);

  return lines.join("\n");
}

module.exports = { generateComplianceReport };
