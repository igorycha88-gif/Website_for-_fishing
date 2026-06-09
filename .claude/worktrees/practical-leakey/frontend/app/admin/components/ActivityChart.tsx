"use client";

import { motion } from "framer-motion";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { LucideIcon } from "lucide-react";

interface ChartDataPoint {
  date: string;
  value: number;
}

interface ActivityChartProps {
  title: string;
  data: ChartDataPoint[];
  icon: LucideIcon;
  color?: string;
  period?: string;
  total?: number;
  average?: number;
}

export default function ActivityChart({
  title,
  data,
  icon: Icon,
  color = "#3b82f6",
  period = "30 дней",
  total,
  average,
}: ActivityChartProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-2xl shadow-lg p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ backgroundColor: `${color}20` }}>
            <Icon className="w-5 h-5" style={{ color }} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-500">За {period}</p>
          </div>
        </div>
        {total !== undefined && average !== undefined && (
          <div className="text-right">
            <p className="text-2xl font-bold" style={{ color }}>
              {total.toLocaleString("ru-RU")}
            </p>
            <p className="text-sm text-gray-500">
              Среднее: {average.toLocaleString("ru-RU")}
            </p>
          </div>
        )}
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#9ca3af"
              fontSize={12}
            />
            <YAxis
              stroke="#9ca3af"
              fontSize={12}
              tickFormatter={(value) => value.toLocaleString("ru-RU")}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #e5e7eb",
                borderRadius: "8px",
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
              }}
              labelFormatter={(label) => formatDate(label)}
              formatter={(value?: number) => [value?.toLocaleString("ru-RU") ?? "0", title]}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={{ fill: color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: color, strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
