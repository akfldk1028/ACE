import { Card, Badge, Button } from '@/shared/ui'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api'
import { GalleryHorizontalEnd, Plus, Download } from 'lucide-react'
import type { Gallery } from '@/shared/types/datamodel'

export function GalleryPage() {
  const { data: galleries, isLoading } = useQuery({
    queryKey: ['galleries'],
    queryFn: api.getGalleries,
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">Gallery</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Reusable agent team templates
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          New Gallery
        </Button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-4 bg-(--color-background-secondary) rounded w-3/4" />
              <div className="h-3 bg-(--color-background-secondary) rounded w-1/2 mt-3" />
              <div className="h-8 bg-(--color-background-secondary) rounded w-20 mt-4" />
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {galleries?.map((gallery: Gallery) => (
            <GalleryCard key={gallery.id} gallery={gallery} />
          ))}
          {(!galleries || galleries.length === 0) && (
            <Card className="col-span-full text-center py-12">
              <p className="text-body-large text-(--color-text-secondary)">
                No gallery items yet. Create templates from the Team Builder.
              </p>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}

function GalleryCard({ gallery }: { gallery: Gallery }) {
  const name = gallery.config?.name ?? `Gallery #${gallery.id}`
  const description = gallery.config?.metadata?.description ?? 'Team template'
  const teamCount = gallery.config?.components?.teams?.length ?? 0
  const agentCount = gallery.config?.components?.agents?.length ?? 0

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-(--color-background-secondary) flex items-center justify-center shrink-0">
          <GalleryHorizontalEnd className="w-5 h-5 text-(--color-text-secondary)" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-heading-small truncate">{name}</h3>
          <p className="text-body-small text-(--color-text-tertiary) mt-1 line-clamp-2">
            {description}
          </p>
          <div className="flex items-center gap-2 mt-2">
            {teamCount > 0 && <Badge variant="primary">{teamCount} teams</Badge>}
            {agentCount > 0 && <Badge variant="outline">{agentCount} agents</Badge>}
          </div>
        </div>
      </div>
      <div className="flex gap-2 mt-4">
        <Button size="sm" variant="primary">
          <Download className="w-3.5 h-3.5 mr-1.5" />
          Import
        </Button>
      </div>
    </Card>
  )
}
