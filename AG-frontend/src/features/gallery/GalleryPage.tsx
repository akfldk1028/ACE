import { memo, useState, useCallback } from 'react'
import { Card, Badge, Button } from '@/shared/ui'
import { GalleryHorizontalEnd, Plus, Download, RefreshCw } from 'lucide-react'
import { useGalleries } from './useGallery'
import { GalleryImportDialog, GallerySyncDialog, GalleryDetail } from './components'
import type { Gallery } from '@/shared/types/datamodel'

export function GalleryPage() {
  const { data: galleries, isLoading } = useGalleries()
  const [importTarget, setImportTarget] = useState<Gallery | null>(null)
  const [syncOpen, setSyncOpen] = useState(false)
  const [selectedGalleryId, setSelectedGalleryId] = useState<number | null>(null)

  const handleImport = useCallback((gallery: Gallery) => {
    setImportTarget(gallery)
  }, [])
  const handleCloseImport = useCallback(() => setImportTarget(null), [])
  const handleCloseSync = useCallback(() => setSyncOpen(false), [])

  const handleSelectGallery = useCallback((gallery: Gallery) => {
    setSelectedGalleryId(gallery.id ?? null)
  }, [])

  const handleBackToList = useCallback(() => {
    setSelectedGalleryId(null)
  }, [])

  // Find the selected gallery object
  const selectedGallery = selectedGalleryId !== null
    ? galleries?.find((g: Gallery) => g.id === selectedGalleryId) ?? null
    : null

  // -- Detail view --
  if (selectedGallery) {
    return (
      <div className="space-y-6">
        <GalleryDetail gallery={selectedGallery} onBack={handleBackToList} />
      </div>
    )
  }

  // -- List view --
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-medium">Gallery</h1>
          <p className="text-body-medium text-(--color-text-secondary) mt-1">
            Reusable agent team templates
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={() => setSyncOpen(true)}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Sync Gallery
          </Button>
          <Button disabled title="Coming soon">
            <Plus className="w-4 h-4 mr-2" />
            New Gallery
          </Button>
        </div>
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
            <GalleryCard
              key={gallery.id}
              gallery={gallery}
              onImport={() => handleImport(gallery)}
              onSelect={() => handleSelectGallery(gallery)}
            />
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

      {/* Dialogs */}
      <GalleryImportDialog gallery={importTarget} onClose={handleCloseImport} />
      <GallerySyncDialog open={syncOpen} onClose={handleCloseSync} />
    </div>
  )
}

const GalleryCard = memo(function GalleryCard({
  gallery,
  onImport,
  onSelect,
}: {
  gallery: Gallery
  onImport: () => void
  onSelect: () => void
}) {
  const config = gallery.config
  const name = config?.name ?? `Gallery #${gallery.id}`
  const description = config?.metadata?.description ?? 'Team template'
  const teamCount = config?.components?.teams?.length ?? 0
  const agentCount = config?.components?.agents?.length ?? 0
  const modelCount = config?.components?.models?.length ?? 0
  const toolCount = config?.components?.tools?.length ?? 0
  const totalCount = teamCount + agentCount + modelCount + toolCount

  const handleCardClick = useCallback(() => {
    onSelect()
  }, [onSelect])

  const handleCardKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onSelect()
      }
    },
    [onSelect]
  )

  const handleImportClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation()
      onImport()
    },
    [onImport]
  )

  return (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer"
      role="button"
      tabIndex={0}
      aria-label={`View gallery: ${name}`}
      onClick={handleCardClick}
      onKeyDown={handleCardKeyDown}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-(--color-background-secondary) flex items-center justify-center shrink-0">
          <GalleryHorizontalEnd className="w-5 h-5 text-(--color-text-secondary)" aria-hidden="true" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-heading-small truncate">{name}</h3>
          <p className="text-body-small text-(--color-text-tertiary) mt-1 line-clamp-2">
            {description}
          </p>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            {teamCount > 0 && (
              <span className="inline-block"><Badge variant="primary">{teamCount} teams</Badge></span>
            )}
            {agentCount > 0 && (
              <span className="inline-block"><Badge variant="outline">{agentCount} agents</Badge></span>
            )}
            {modelCount > 0 && (
              <span className="inline-block"><Badge variant="default">{modelCount} models</Badge></span>
            )}
            {toolCount > 0 && (
              <span className="inline-block"><Badge variant="default">{toolCount} tools</Badge></span>
            )}
            {totalCount === 0 && (
              <span className="text-body-small text-(--color-text-tertiary)">Empty</span>
            )}
          </div>
        </div>
      </div>
      <div className="flex gap-2 mt-4">
        <Button
          size="sm"
          variant="primary"
          onClick={handleImportClick}
          aria-label={`Import team from ${name}`}
        >
          <Download className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
          Import
        </Button>
      </div>
    </Card>
  )
})
