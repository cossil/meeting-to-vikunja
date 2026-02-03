import React from 'react';
import { TaskState, Assignee } from '../types';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface DraftBoardProps {
  task: TaskState;
}

const DraftBoard: React.FC<DraftBoardProps> = ({ task }) => {
  
  // Calculate completeness for the chart
  const fields = ['title', 'description', 'dueDate', 'assignee'];
  const filledCount = fields.filter(f => task[f as keyof TaskState] !== null).length;
  const data = [
    { name: 'Preenchido', value: filledCount },
    { name: 'Pendente', value: fields.length - filledCount },
  ];
  const COLORS = ['#10b981', '#e2e8f0']; // Green-500, Slate-200

  return (
    <div className="bg-white border-l border-slate-200 h-full flex flex-col shadow-lg transition-all duration-300 w-full md:w-80 lg:w-96">
      <div className="p-6 bg-slate-900 text-white">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>
          Quadro de Rascunho
        </h2>
        <p className="text-xs text-slate-400 mt-1">Atualizado em tempo real</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {/* Status Badge */}
        <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500 uppercase tracking-wider">Status</span>
            <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                task.status === 'Completo' ? 'bg-green-100 text-green-700' :
                task.status === 'A Revisar' ? 'bg-amber-100 text-amber-700' :
                'bg-blue-100 text-blue-700'
            }`}>
                {task.status.toUpperCase()}
            </span>
        </div>

        {/* Completeness Chart */}
        <div className="h-40 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={60}
                        fill="#8884d8"
                        paddingAngle={5}
                        dataKey="value"
                        stroke="none"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip />
                </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                 <span className="text-2xl font-bold text-slate-700">{Math.round((filledCount / fields.length) * 100)}%</span>
            </div>
        </div>

        {/* Fields */}
        <div className="space-y-4">
            <DraftField label="Título" value={task.title} isMissing={task.missingInfo.includes('title')} />
            <DraftField label="Responsável" value={task.assignee} isMissing={task.missingInfo.includes('assignee')} />
            <DraftField label="Data Limite" value={task.dueDate} isMissing={task.missingInfo.includes('dueDate')} />
            
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
                <span className="block text-xs font-semibold text-slate-400 uppercase mb-1">Descrição</span>
                <p className={`text-sm ${task.description ? 'text-slate-800' : 'text-slate-400 italic'}`}>
                    {task.description || "Aguardando detalhes..."}
                </p>
            </div>
        </div>

        {/* Raw JSON Debug (Optional but requested "JSON view") */}
        <div className="mt-8 pt-6 border-t border-slate-100">
            <h3 className="text-xs font-mono text-slate-400 mb-2">JSON VIEW</h3>
            <pre className="bg-slate-900 text-green-400 p-3 rounded text-[10px] overflow-x-auto leading-relaxed">
                {JSON.stringify(task, null, 2)}
            </pre>
        </div>
      </div>
    </div>
  );
};

const DraftField = ({ label, value, isMissing }: { label: string, value: string | null, isMissing: boolean }) => (
    <div className={`p-3 rounded-lg border transition-colors ${
        isMissing 
        ? 'border-dashed border-slate-300 bg-slate-50' 
        : 'border-solid border-emerald-200 bg-emerald-50/50'
    }`}>
        <span className="block text-xs font-semibold text-slate-500 uppercase mb-1">{label}</span>
        <div className={`text-sm font-medium ${value ? 'text-slate-900' : 'text-slate-400 italic'}`}>
            {value || "—"}
        </div>
    </div>
);

export default DraftBoard;
