import { useBatchStore } from '../store/useBatchStore';
import { Layout } from './layout/Layout';
import { FileUpload } from './batch/FileUpload';
import { TaskReviewGrid } from './batch/TaskReviewGrid';
import { Button } from './ui/button';
import { Loader2, CheckCircle2, ArrowRight } from 'lucide-react';

export function BatchProcessingView() {
    const { tasks, status, syncToVikunja, syncResult, reset } = useBatchStore();


    const showGrid = tasks.length > 0 && status !== 'completed';
    const showSuccess = status === 'completed' && syncResult;

    return (
        <Layout>
            <div className="container mx-auto max-w-7xl h-[calc(100vh-100px)] flex flex-col space-y-6">
                {showGrid && (
                    <div className="flex items-center justify-between mb-6 shrink-0">
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight">Review Tasks</h1>
                            <p className="text-muted-foreground">
                                Found {tasks.length} tasks. Review and edit before syncing.
                            </p>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" onClick={() => reset()}>
                                Cancel
                            </Button>
                            <Button onClick={() => syncToVikunja()} disabled={status === 'syncing'}>
                                {status === 'syncing' && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                                Sync {tasks.length} Tasks to Vikunja
                            </Button>
                        </div>
                    </div>
                )}

                {/* Success View */}
                {showSuccess && (
                    <div className="flex flex-col items-center justify-center space-y-4 py-20 text-center">
                        <div className="h-16 w-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                            <CheckCircle2 className="w-8 h-8" />
                        </div>
                        <div className="space-y-2">
                            <h2 className="text-2xl font-bold">Sync Complete!</h2>
                            <p className="text-muted-foreground">
                                Successfully synced {syncResult.success} tasks to Vikunja.
                            </p>
                        </div>
                        <Button onClick={() => reset()} className="mt-4">
                            Process More Files <ArrowRight className="ml-2 w-4 h-4" />
                        </Button>
                    </div>
                )}

                {/* Main Content Content Switcher */}
                {!showGrid && !showSuccess && (
                    <FileUpload />
                )}

                {showGrid && (
                    <TaskReviewGrid />
                )}
            </div>
        </Layout>
    );
}
