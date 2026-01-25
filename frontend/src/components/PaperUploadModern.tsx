import React, { useState, useCallback } from 'react'
import axios from 'axios'
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface UploadedFile {
  file: File
  status: 'uploading' | 'success' | 'error'
  response?: any
  error?: string
  progress?: number
}

interface PaperUploadModernProps {
  onUploadComplete?: (papers: any[]) => void
}

const PaperUploadModern: React.FC<PaperUploadModernProps> = ({ onUploadComplete }) => {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf'
    )
    
    if (droppedFiles.length > 0) {
      handleFileUpload(droppedFiles)
    }
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files
    if (selectedFiles && selectedFiles.length > 0) {
      const pdfFiles = Array.from(selectedFiles).filter(
        file => file.type === 'application/pdf'
      )
      handleFileUpload(pdfFiles)
    }
    // Reset input
    e.target.value = ''
  }, [])

  const handleFileUpload = async (newFiles: File[]) => {
    setIsUploading(true)
    
    // Add files to state with uploading status
    const uploadFiles: UploadedFile[] = newFiles.map(file => ({
      file,
      status: 'uploading' as const,
      progress: 0
    }))
    
    setFiles(prev => [...prev, ...uploadFiles])
    
    // Upload each file
    const uploadPromises = newFiles.map(async (file, _index) => {
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        const response = await axios.post('http://localhost:8000/api/papers/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
              setFiles(prev => prev.map((f, _i) => 
                f.file === file ? { ...f, progress } : f
              ))
            }
          }
        })
        
        // Update file status to success
        setFiles(prev => prev.map(f => 
          f.file === file 
            ? { ...f, status: 'success' as const, response: response.data }
            : f
        ))
        
        return response.data
      } catch (error: any) {
        // Update file status to error
        setFiles(prev => prev.map(f => 
          f.file === file 
            ? { 
                ...f, 
                status: 'error' as const, 
                error: error.response?.data?.detail || 'Upload failed'
              }
            : f
        ))
        
        return null
      }
    })
    
    const results = await Promise.all(uploadPromises)
    const successfulUploads = results.filter(Boolean)
    
    setIsUploading(false)
    
    if (onUploadComplete && successfulUploads.length > 0) {
      onUploadComplete(successfulUploads)
    }
  }

  const removeFile = useCallback((fileToRemove: File) => {
    setFiles(prev => prev.filter(f => f.file !== fileToRemove))
  }, [])

  const clearAll = useCallback(() => {
    setFiles([])
  }, [])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
    }
  }

  const getStatusBadge = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800">Uploading</Badge>
      case 'success':
        return <Badge variant="secondary" className="bg-green-100 text-green-800">Success</Badge>
      case 'error':
        return <Badge variant="secondary" className="bg-red-100 text-red-800">Error</Badge>
    }
  }

  const successCount = files.filter(f => f.status === 'success').length
  const errorCount = files.filter(f => f.status === 'error').length
  const uploadingCount = files.filter(f => f.status === 'uploading').length

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Upload Research Papers
          </CardTitle>
          <CardDescription>
            Upload PDF research papers to analyze and extract insights. Drag and drop files or click to browse.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`
              relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${isDragging 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
              ${isUploading ? 'opacity-50 pointer-events-none' : ''}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="space-y-4">
              <div className="mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-gray-100">
                <Upload className="h-8 w-8 text-gray-500" />
              </div>
              
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {isDragging ? 'Drop PDF files here' : 'Upload research papers'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Drag and drop PDF files here, or click to browse
                </p>
              </div>
              
              <div className="flex items-center justify-center">
                <Button
                  variant="outline"
                  disabled={isUploading}
                  onClick={() => document.getElementById('file-upload')?.click()}
                >
                  {isUploading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Choose Files
                    </>
                  )}
                </Button>
              </div>
              
              <p className="text-xs text-gray-400">
                PDF files only • Max 50MB per file
              </p>
            </div>
            
            <input
              id="file-upload"
              type="file"
              accept=".pdf"
              multiple
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={handleFileSelect}
              disabled={isUploading}
            />
          </div>
        </CardContent>
      </Card>

      {/* Upload Progress and Results */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                Upload Progress
                <Badge variant="outline">
                  {files.length} file{files.length !== 1 ? 's' : ''}
                </Badge>
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={clearAll}>
                <X className="h-4 w-4 mr-2" />
                Clear All
              </Button>
            </div>
            
            {/* Summary badges */}
            <div className="flex gap-2">
              {successCount > 0 && (
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  {successCount} successful
                </Badge>
              )}
              {uploadingCount > 0 && (
                <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                  {uploadingCount} uploading
                </Badge>
              )}
              {errorCount > 0 && (
                <Badge variant="secondary" className="bg-red-100 text-red-800">
                  {errorCount} failed
                </Badge>
              )}
            </div>
          </CardHeader>
          
          <CardContent>
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {files.map((uploadedFile, index) => (
                  <div key={index} className="flex items-start justify-between p-3 border rounded-lg">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      {getStatusIcon(uploadedFile.status)}
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="text-sm font-medium truncate">
                            {uploadedFile.file.name}
                          </p>
                          {getStatusBadge(uploadedFile.status)}
                        </div>
                        
                        <p className="text-xs text-gray-500 mb-2">
                          {formatFileSize(uploadedFile.file.size)}
                        </p>
                        
                        {/* Progress bar for uploading files */}
                        {uploadedFile.status === 'uploading' && uploadedFile.progress !== undefined && (
                          <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                            <div 
                              className="bg-blue-600 h-1.5 rounded-full transition-all duration-300" 
                              style={{ width: `${uploadedFile.progress}%` }}
                            />
                          </div>
                        )}
                        
                        {/* Success details */}
                        {uploadedFile.status === 'success' && uploadedFile.response && (
                          <div className="text-xs space-y-1">
                            <p className="text-green-700 font-medium">
                              ✓ {uploadedFile.response.message}
                            </p>
                            <div className="text-gray-600">
                              <span className="font-medium">Title:</span> {uploadedFile.response.title}
                            </div>
                            <div className="flex gap-4 text-gray-500">
                              <span>{uploadedFile.response.extracted_sections} sections</span>
                              <span>{uploadedFile.response.extracted_authors} authors</span>
                            </div>
                          </div>
                        )}
                        
                        {/* Error details */}
                        {uploadedFile.status === 'error' && uploadedFile.error && (
                          <Alert className="mt-2">
                            <AlertCircle className="h-4 w-4" />
                            <AlertDescription className="text-xs">
                              {uploadedFile.error}
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(uploadedFile.file)}
                      className="ml-2 flex-shrink-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
      
      {/* Success message */}
      {successCount > 0 && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Successfully uploaded {successCount} paper{successCount !== 1 ? 's' : ''}. 
            You can now browse and analyze them in the Papers section.
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default PaperUploadModern