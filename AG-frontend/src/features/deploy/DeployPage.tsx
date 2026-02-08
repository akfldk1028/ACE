import { Card, Badge } from '@/shared/ui'
import { Rocket, Container, Terminal, Cloud } from 'lucide-react'

const DEPLOY_GUIDES = [
  {
    title: 'Docker Deployment',
    icon: Container,
    description: 'Deploy AutoGen Studio as a Docker container with all dependencies included.',
    badge: 'Recommended',
    steps: [
      'docker pull autogenstudio:latest',
      'docker run -p 8081:8081 autogenstudio:latest',
      'Open http://localhost:8081 in your browser',
    ],
  },
  {
    title: 'Python Server',
    icon: Terminal,
    description: 'Run AutoGen Studio directly with Python for development and testing.',
    badge: 'Development',
    steps: [
      'pip install autogenstudio',
      'autogenstudio ui --port 8081',
      'Open http://localhost:8081 in your browser',
    ],
  },
  {
    title: 'Cloud Deployment',
    icon: Cloud,
    description: 'Deploy to cloud platforms like Azure, AWS, or GCP.',
    badge: 'Production',
    steps: [
      'Configure environment variables',
      'Set up database (PostgreSQL recommended)',
      'Deploy with your cloud provider CLI',
    ],
  },
]

export function DeployPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-display-medium">Deploy</h1>
        <p className="text-body-medium text-(--color-text-secondary) mt-1">
          Deployment guides and configuration
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {DEPLOY_GUIDES.map((guide) => (
          <Card key={guide.title} className="hover:shadow-lg transition-shadow">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-(--color-background-secondary) flex items-center justify-center">
                <guide.icon className="w-5 h-5 text-(--color-text-secondary)" />
              </div>
              <div>
                <h2 className="text-heading-small">{guide.title}</h2>
                <Badge variant="outline">{guide.badge}</Badge>
              </div>
            </div>
            <p className="text-body-medium text-(--color-text-tertiary) mb-4">
              {guide.description}
            </p>
            <div className="space-y-2">
              {guide.steps.map((step, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-label-small text-(--color-accent-primary) shrink-0 mt-0.5">
                    {i + 1}.
                  </span>
                  <code className="text-body-small font-mono bg-(--color-background-secondary) px-2 py-1 rounded text-(--color-text-primary) break-all">
                    {step}
                  </code>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>

      <Card>
        <div className="flex items-center gap-3 mb-4">
          <Rocket className="w-5 h-5 text-(--color-text-secondary)" />
          <h2 className="text-heading-small">Current Instance</h2>
        </div>
        <p className="text-body-medium text-(--color-text-tertiary)">
          AutoGen Studio is running at <code className="bg-(--color-background-secondary) px-1.5 py-0.5 rounded">localhost:8081</code>.
          The AG Frontend connects via Vite proxy at <code className="bg-(--color-background-secondary) px-1.5 py-0.5 rounded">localhost:5173</code>.
        </p>
      </Card>
    </div>
  )
}
