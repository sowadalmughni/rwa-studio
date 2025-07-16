import { useState } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { CheckCircle, Circle, Building, FileText, DollarSign, Users, Rocket } from 'lucide-react'
import './App.css'

function App() {
  const [currentStep, setCurrentStep] = useState(1)
  const [completedSteps, setCompletedSteps] = useState([])
  const [tokenData, setTokenData] = useState({
    assetType: '',
    regulatoryFramework: '',
    tokenEconomics: {},
    investorRestrictions: {},
    deployment: {}
  })

  const steps = [
    {
      id: 1,
      title: 'Asset Type Selection',
      description: 'Choose your asset category',
      icon: Building,
      options: [
        { id: 'real-estate', label: 'Real Estate', description: 'Properties, REITs, land' },
        { id: 'private-equity', label: 'Private Equity', description: 'Fund shares, equity stakes' },
        { id: 'debt', label: 'Debt Instruments', description: 'Bonds, loans, credit' },
        { id: 'commodities', label: 'Commodities', description: 'Gold, oil, agricultural' },
        { id: 'ip', label: 'Intellectual Property', description: 'Patents, royalties, licenses' }
      ]
    },
    {
      id: 2,
      title: 'Regulatory Framework',
      description: 'Select compliance requirements',
      icon: FileText,
      options: [
        { id: 'reg-d', label: 'Regulation D', description: 'US private placements' },
        { id: 'reg-s', label: 'Regulation S', description: 'International offerings' },
        { id: 'reg-cf', label: 'Regulation CF', description: 'Crowdfunding exemption' },
        { id: 'custom', label: 'Custom Framework', description: 'Jurisdiction-specific' }
      ]
    },
    {
      id: 3,
      title: 'Token Economics',
      description: 'Configure supply and distribution',
      icon: DollarSign,
      fields: ['totalSupply', 'initialPrice', 'vestingSchedule', 'dividendStructure']
    },
    {
      id: 4,
      title: 'Investor Restrictions',
      description: 'Set compliance and transfer rules',
      icon: Users,
      fields: ['kycRequirements', 'geographicRestrictions', 'investorLimits', 'transferRules']
    },
    {
      id: 5,
      title: 'Deployment & Asset Page',
      description: 'Deploy contracts and generate page',
      icon: Rocket,
      final: true
    }
  ]

  const handleStepComplete = (stepId, data) => {
    setCompletedSteps([...completedSteps, stepId])
    setTokenData({ ...tokenData, ...data })
    if (stepId < 5) {
      setCurrentStep(stepId + 1)
    }
  }

  const progress = (completedSteps.length / 5) * 100

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-gray-900">RWA-Studio</h1>
                <p className="text-sm text-gray-500">Tokenize Real-World Assets in 5 Clicks</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                🔒 ERC-3643 Compliant
              </Badge>
              <Button variant="outline">Connect Wallet</Button>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm text-gray-500">{completedSteps.length}/5 steps completed</span>
          </div>
          <Progress value={progress} className="w-full" />
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Steps Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Tokenization Steps</CardTitle>
                <CardDescription>Follow the 5-click workflow</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {steps.map((step) => {
                  const Icon = step.icon
                  const isCompleted = completedSteps.includes(step.id)
                  const isCurrent = currentStep === step.id
                  
                  return (
                    <div
                      key={step.id}
                      className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                        isCurrent ? 'bg-blue-50 border border-blue-200' : 
                        isCompleted ? 'bg-green-50' : 'bg-gray-50'
                      }`}
                    >
                      <div className={`flex-shrink-0 ${
                        isCompleted ? 'text-green-600' : 
                        isCurrent ? 'text-blue-600' : 'text-gray-400'
                      }`}>
                        {isCompleted ? <CheckCircle size={20} /> : <Circle size={20} />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium ${
                          isCurrent ? 'text-blue-900' : 
                          isCompleted ? 'text-green-900' : 'text-gray-900'
                        }`}>
                          {step.title}
                        </p>
                        <p className="text-xs text-gray-500">{step.description}</p>
                      </div>
                      <Icon size={16} className={
                        isCompleted ? 'text-green-600' : 
                        isCurrent ? 'text-blue-600' : 'text-gray-400'
                      } />
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          </div>

          {/* Main Step Content */}
          <div className="lg:col-span-3">
            <StepContent 
              step={steps.find(s => s.id === currentStep)}
              onComplete={handleStepComplete}
              tokenData={tokenData}
            />
          </div>
        </div>
      </main>
    </div>
  )
}

function StepContent({ step, onComplete, tokenData }) {
  const [selectedOption, setSelectedOption] = useState('')
  const [formData, setFormData] = useState({})

  const handleOptionSelect = (optionId) => {
    setSelectedOption(optionId)
  }

  const handleSubmit = () => {
    if (step.options) {
      onComplete(step.id, { [step.title.toLowerCase().replace(/\s+/g, '')]: selectedOption })
    } else if (step.fields) {
      onComplete(step.id, { [step.title.toLowerCase().replace(/\s+/g, '')]: formData })
    } else {
      // Final step
      onComplete(step.id, { deployment: { status: 'completed' } })
    }
  }

  const Icon = step.icon

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Icon className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <CardTitle className="text-xl">{step.title}</CardTitle>
            <CardDescription>{step.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {step.options && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {step.options.map((option) => (
              <div
                key={option.id}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                  selectedOption === option.id 
                    ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleOptionSelect(option.id)}
              >
                <h3 className="font-medium text-gray-900 mb-1">{option.label}</h3>
                <p className="text-sm text-gray-500">{option.description}</p>
              </div>
            ))}
          </div>
        )}

        {step.fields && (
          <div className="space-y-4">
            <p className="text-gray-600">Configure your token economics and restrictions:</p>
            {step.fields.map((field) => (
              <div key={field} className="p-4 border border-gray-200 rounded-lg">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {field.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={`Enter ${field.toLowerCase()}`}
                  onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
                />
              </div>
            ))}
          </div>
        )}

        {step.final && (
          <div className="text-center space-y-4">
            <div className="p-8 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
              <Rocket className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Ready to Deploy!</h3>
              <p className="text-gray-600 mb-4">
                Your compliant security token is ready for deployment. This will create your smart contracts 
                and generate a shareable asset page with compliance badges.
              </p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-white p-3 rounded border">
                  <strong>Asset Type:</strong> {tokenData.assettypeselection || 'Not selected'}
                </div>
                <div className="bg-white p-3 rounded border">
                  <strong>Framework:</strong> {tokenData.regulatoryframework || 'Not selected'}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-between pt-6">
          <Button 
            variant="outline" 
            disabled={step.id === 1}
            onClick={() => window.location.reload()}
          >
            Reset
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={step.options ? !selectedOption : step.fields ? Object.keys(formData).length === 0 : false}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {step.final ? 'Deploy Token' : 'Continue'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default App

