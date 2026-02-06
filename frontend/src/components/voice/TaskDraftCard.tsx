
import { useVoiceStore } from '../../store/useVoiceStore';
import { Card } from '../ui/card';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Sparkles, CheckCircle, Calendar as CalendarIcon, User as UserIcon, Loader2 } from 'lucide-react';
import type { VoiceState } from '../../types/schema';

export function TaskDraftCard() {
    const { currentTask, updateCurrentTask, isProcessing, resetCurrentTask, syncToVikunja } = useVoiceStore();

    // Helper to update fields
    const updateField = (field: keyof VoiceState, value: any) => {
        updateCurrentTask({ [field]: value });
    };

    return (
        <div className="flex-1 bg-gray-50 dark:bg-black/20 p-8 overflow-y-auto flex flex-col items-center justify-start pt-12">
            <div className="w-full max-w-lg">
                {/* Header */}
                <div className="flex items-center justify-between mb-4 px-1">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary" />
                        Rascunho
                    </h2>
                    {isProcessing && (
                        <Badge variant="outline" className="animate-pulse border-primary text-primary bg-primary/10">
                            Escrevendo...
                        </Badge>
                    )}
                </div>

                {/* Form Card */}
                <Card className="rounded-xl shadow-sm border-gray-200 dark:border-gray-800 overflow-hidden">
                    <div className="p-6 space-y-6">
                        {/* Title */}
                        <div className="space-y-1.5">
                            <Label className="text-xs font-semibold uppercase tracking-wider text-gray-500">Título</Label>
                            <Input
                                value={currentTask.title || ''}
                                onChange={(e) => updateField('title', e.target.value)}
                                className="text-lg font-semibold border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
                                placeholder="Título da tarefa..."
                            />
                        </div>

                        {/* Description */}
                        <div className="space-y-1.5">
                            <Label className="text-xs font-semibold uppercase tracking-wider text-gray-500">Descrição</Label>
                            <Textarea
                                value={currentTask.description || ''}
                                onChange={(e) => updateField('description', e.target.value)}
                                className="min-h-[120px] border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 resize-y"
                                placeholder="Descrição da tarefa..."
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            {/* Assignee */}
                            <div className="space-y-1.5">
                                <Label className="text-xs font-semibold uppercase tracking-wider text-gray-500">Responsável</Label>
                                <div className="relative">
                                    <UserIcon className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        value={currentTask.assignee || ''}
                                        onChange={(e) => updateField('assignee', e.target.value)}
                                        className="pl-9"
                                        placeholder="Não atribuído"
                                    />
                                </div>
                            </div>

                            {/* Due Date */}
                            <div className="space-y-1.5">
                                <Label className="text-xs font-semibold uppercase tracking-wider text-gray-500">Vencimento</Label>
                                <div className="relative">
                                    <CalendarIcon className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        type="date"
                                        value={currentTask.dueDate || ''}
                                        onChange={(e) => updateField('dueDate', e.target.value)}
                                        className="pl-9"
                                    />
                                </div>
                            </div>

                            {/* Priority */}
                            <div className="space-y-1.5">
                                <Label className="text-xs font-semibold uppercase tracking-wider text-gray-500">Prioridade</Label>
                                <Select
                                    value={currentTask.priority?.toString() || '3'}
                                    onValueChange={(val) => updateField('priority', parseInt(val))}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Prioridade" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="1">Baixa</SelectItem>
                                        <SelectItem value="2">Média</SelectItem>
                                        <SelectItem value="3">Alta</SelectItem>
                                        <SelectItem value="4">Urgente</SelectItem>
                                        <SelectItem value="5">Crítica</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="bg-gray-50 dark:bg-gray-800/80 p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                        <Button variant="ghost" onClick={resetCurrentTask} disabled={isProcessing}>Descartar</Button>
                        <Button
                            className="gap-2"
                            onClick={() => syncToVikunja()}
                            disabled={isProcessing || !currentTask.title}
                        >
                            {isProcessing ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <CheckCircle className="w-4 h-4" />
                            )}
                            Criar Tarefa
                        </Button>
                    </div>
                </Card>
            </div>
        </div>
    );
}
