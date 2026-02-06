import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useBatchStore } from '../store/useBatchStore';
import { Card, CardContent } from './ui/card';
import { UploadCloud, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';

// Minimal Alert component implementation inside file to avoid extra file creation if possible, 
// but sticking to standard Shadcn pattern is better. 
// I'll create a simple Alert inline visually or assume it exists. 
// Actually, I'll use simple div styling for alert for now to save a tool call or use standard colors.

export function FileUpload() {
    const { uploadFiles, status, error } = useBatchStore();

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            uploadFiles(acceptedFiles);
        }
    }, [uploadFiles]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    return (
        <div className="max-w-2xl mx-auto mt-10 space-y-6">
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold tracking-tight">Upload Meeting Notes</h2>
                <p className="text-muted-foreground">
                    Upload your meeting transcripts or notes (.txt) to extract tasks.
                </p>
            </div>

            {error && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            <Card
                {...getRootProps()}
                className={cn(
                    "border-2 border-dashed cursor-pointer transition-colors hover:bg-muted/50",
                    isDragActive && "border-primary bg-primary/5",
                    status === 'uploading' && "opacity-50 pointer-events-none"
                )}
            >
                <CardContent className="flex flex-col items-center justify-center py-20 text-center space-y-4">
                    <input {...getInputProps()} />

                    <div className="p-4 bg-muted rounded-full">
                        {status === 'uploading' ? (
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        ) : (
                            <UploadCloud className="w-8 h-8 text-muted-foreground" />
                        )}
                    </div>

                    <div className="space-y-1">
                        <p className="font-medium">
                            {status === 'uploading'
                                ? "Analyzing files..."
                                : isDragActive
                                    ? "Drop the files here"
                                    : "Click or drag files to upload"
                            }
                        </p>
                        <p className="text-sm text-muted-foreground">
                            Supports .txt files
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
