
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useBatchStore } from '../../store/useBatchStore';
import { Card, CardContent } from '../ui/card';
import { Upload, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';

export function FileUpload() {
    const { uploadFiles, status, error } = useBatchStore();

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            uploadFiles(acceptedFiles);
        }
    }, [uploadFiles]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

    return (
        <div className="w-full">
            {error && (
                <Alert variant="destructive" className="mb-6">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                </Alert>
            )}

            <div
                {...getRootProps()}
                className={cn(
                    "group relative flex flex-col items-center justify-center w-full h-48 rounded-xl border-2 border-dashed transition-all cursor-pointer",
                    isDragActive
                        ? "border-primary bg-primary/5"
                        : "border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-primary/50 hover:bg-primary/5",
                    status === 'uploading' && "opacity-50 pointer-events-none"
                )}
            >
                <input {...getInputProps()} />

                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <div className={cn(
                        "p-3 rounded-full mb-3 transition-transform duration-200 group-hover:scale-110",
                        isDragActive ? "bg-primary/20" : "bg-gray-100 dark:bg-gray-700"
                    )}>
                        {status === 'uploading' ? (
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        ) : (
                            <Upload className="w-8 h-8 text-gray-500 dark:text-gray-400 group-hover:text-primary" />
                        )}
                    </div>

                    <p className="mb-1 text-lg font-medium text-gray-700 dark:text-gray-300">
                        {status === 'uploading' ? (
                            "Analyzing files..."
                        ) : (
                            <>
                                <span className="text-primary hover:underline">Click to upload</span> or drag and drop
                            </>
                        )}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Supported formats: .txt, .docx, .vtt (Max 25MB)
                    </p>
                </div>
            </div>
        </div>
    );
}
