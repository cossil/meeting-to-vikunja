
import { useBatchStore } from '../../store/useBatchStore';
import { cn } from '../../lib/utils';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from '../ui/table';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Checkbox } from '../ui/checkbox';
import { Badge } from '../ui/badge';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '../ui/select';
import { Trash2 } from 'lucide-react';
import type { Task } from '../../types/schema';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';

export function TaskReviewGrid() {
    const { tasks, updateTask, removeTask } = useBatchStore();

    const handleUpdate = (index: number, field: keyof Task, value: any) => {
        updateTask(index, { [field]: value });
    };

    const getPriorityColor = (priority: number) => {
        switch (priority) {
            case 5: return "bg-red-600 hover:bg-red-700"; // Critical
            case 4: return "bg-orange-500 hover:bg-orange-600"; // Urgent
            case 3: return "bg-yellow-500 hover:bg-yellow-600"; // High
            case 2: return "bg-blue-500 hover:bg-blue-600"; // Medium
            default: return "bg-gray-500 hover:bg-gray-600"; // Low
        }
    };

    const getPriorityLabel = (priority: number) => {
        switch (priority) {
            case 5: return "Crítica";
            case 4: return "Urgente";
            case 3: return "Alta";
            case 2: return "Média";
            default: return "Baixa";
        }
    }

    if (tasks.length === 0) return null;

    return (
        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm overflow-hidden flex flex-col h-full">
            <div className="flex-1 overflow-y-auto">
                <Table>
                    <TableHeader className="sticky top-0 z-10 bg-gray-50 dark:bg-gray-800 shadow-sm">
                        <TableRow>
                            <TableHead className="w-12 p-4">
                                <Checkbox />
                            </TableHead>
                            <TableHead className="w-[25%] min-w-[250px] whitespace-normal break-words">Título</TableHead>
                            <TableHead className="w-[40%]">Descrição</TableHead>
                            <TableHead className="w-[15%]">Responsável</TableHead>
                            <TableHead className="w-[10%]">Prioridade</TableHead>
                            <TableHead className="w-[12%]">Vencimento</TableHead>
                            <TableHead className="w-[150px] text-right">Ações</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {tasks.map((task, index) => (
                            <TableRow key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 text-lg">
                                <TableCell className="p-4">
                                    <Checkbox />
                                </TableCell>
                                <TableCell>
                                    <Input
                                        value={task.title}
                                        onChange={(e) => handleUpdate(index, 'title', e.target.value)}
                                        placeholder="Título da tarefa"
                                        className="border-transparent bg-transparent shadow-none hover:bg-gray-100 dark:hover:bg-gray-800 focus:bg-white dark:focus:bg-gray-950 font-medium whitespace-normal break-words h-auto py-2 min-w-[250px]"
                                    />
                                </TableCell>

                                <TableCell>
                                    <Textarea
                                        value={task.description || ''}
                                        onChange={(e) => handleUpdate(index, 'description', e.target.value)}
                                        placeholder="Descrição"
                                        className="min-h-[3.5rem] py-2 resize-y border-transparent bg-transparent shadow-none hover:bg-gray-100 dark:hover:bg-gray-800 focus:bg-white dark:focus:bg-gray-950 text-base text-muted-foreground whitespace-normal break-words"
                                    />
                                </TableCell>

                                <TableCell>
                                    <div className="flex items-center gap-2">
                                        <Avatar className="h-6 w-6">
                                            <AvatarImage src={`https://ui-avatars.com/api/?name=${task.assignee_name || 'Unassigned'}`} />
                                            <AvatarFallback>UN</AvatarFallback>
                                        </Avatar>
                                        <Input
                                            value={task.assignee_name || ''}
                                            onChange={(e) => handleUpdate(index, 'assignee_name', e.target.value)}
                                            placeholder="Unassigned"
                                            className="h-8 border-transparent bg-transparent shadow-none hover:bg-gray-100 dark:hover:bg-gray-800 focus:bg-white dark:focus:bg-gray-950"
                                        />
                                    </div>
                                </TableCell>

                                <TableCell>
                                    <Select
                                        value={task.priority.toString()}
                                        onValueChange={(val) => handleUpdate(index, 'priority', parseInt(val))}
                                    >
                                        <SelectTrigger className="w-full h-8 border-transparent bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800">
                                            <SelectValue>
                                                <Badge className={cn("pointer-events-none", getPriorityColor(task.priority))}>
                                                    {getPriorityLabel(task.priority)}
                                                </Badge>
                                            </SelectValue>
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="1">Baixa</SelectItem>
                                            <SelectItem value="2">Média</SelectItem>
                                            <SelectItem value="3">Alta</SelectItem>
                                            <SelectItem value="4">Urgente</SelectItem>
                                            <SelectItem value="5">Crítica</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </TableCell>

                                <TableCell>
                                    <Input
                                        type="date"
                                        value={task.due_date || ''}
                                        onChange={(e) => handleUpdate(index, 'due_date', e.target.value)}
                                        className="h-8 border-transparent bg-transparent shadow-none hover:bg-gray-100 dark:hover:bg-gray-800 focus:bg-white dark:focus:bg-gray-950 text-xs"
                                    />
                                </TableCell>

                                <TableCell className="text-right">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => removeTask(index)}
                                        className="text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
