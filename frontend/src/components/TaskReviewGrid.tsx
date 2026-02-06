import { useBatchStore } from '../store/useBatchStore';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow
} from './ui/table';
import { Input } from './ui/input';
import { Button } from './ui/button';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue
} from './ui/select';
import { Trash2 } from 'lucide-react';
import type { Task } from '../types/schema';

export function TaskReviewGrid() {
    const { tasks, updateTask, removeTask } = useBatchStore();

    const handleUpdate = (index: number, field: keyof Task, value: any) => {
        updateTask(index, { [field]: value });
    };

    if (tasks.length === 0) return null;

    return (
        <div className="rounded-md border">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead className="w-[40%]">Task Title</TableHead>
                        <TableHead className="w-[20%]">Assignee</TableHead>
                        <TableHead className="w-[15%]">Due Date</TableHead>
                        <TableHead className="w-[15%]">Priority</TableHead>
                        <TableHead className="w-[10%]"></TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {tasks.map((task, index) => (
                        <TableRow key={index}>
                            <TableCell>
                                <Input
                                    value={task.title}
                                    onChange={(e) => handleUpdate(index, 'title', e.target.value)}
                                    placeholder="Task title"
                                    className="border-transparent hover:border-input focus:border-input"
                                />
                            </TableCell>

                            <TableCell>
                                <Input
                                    value={task.assignee_name || ''}
                                    onChange={(e) => handleUpdate(index, 'assignee_name', e.target.value)}
                                    placeholder="Unassigned"
                                    className="border-transparent hover:border-input focus:border-input"
                                />
                            </TableCell>

                            <TableCell>
                                <Input
                                    type="date"
                                    value={task.due_date || ''}
                                    onChange={(e) => handleUpdate(index, 'due_date', e.target.value)}
                                    className="border-transparent hover:border-input focus:border-input"
                                />
                            </TableCell>

                            <TableCell>
                                <Select
                                    value={task.priority.toString()}
                                    onValueChange={(val) => handleUpdate(index, 'priority', parseInt(val))}
                                >
                                    <SelectTrigger className="w-full border-transparent hover:border-input focus:border-input">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="1">Low (1)</SelectItem>
                                        <SelectItem value="2">Medium (2)</SelectItem>
                                        <SelectItem value="3">High (3)</SelectItem>
                                        <SelectItem value="4">Urgent (4)</SelectItem>
                                        <SelectItem value="5">Critical (5)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </TableCell>

                            <TableCell>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => removeTask(index)}
                                    className="text-muted-foreground hover:text-destructive"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}
