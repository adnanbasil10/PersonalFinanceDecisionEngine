"use client";

import { useState } from "react";
import Papa from "papaparse";
import { UploadCloud } from "lucide-react";
import { uploadTransactions } from "@/lib/api";

export default function CSVUploader({ onSuccess }: { onSuccess: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (results) => {
        try {
          const formatted = results.data.map((row: any) => ({
            date: row.date,
            amount: parseFloat(row.amount),
            category: row.category,
            merchant: row.merchant || undefined,
            description: row.description || undefined,
          }));

          await uploadTransactions(formatted);
          onSuccess();
        } catch (err: any) {
          setError(err.message || "Failed to process CSV file.");
        } finally {
          setLoading(false);
          e.target.value = ""; // Reset input
        }
      },
      error: (err) => {
        setError(err.message);
        setLoading(false);
      },
    });
  };

  return (
    <div className="mt-4">
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-white/20 rounded-xl cursor-pointer bg-slate-800/30 hover:bg-slate-800/50 hover:border-emerald-500/50 transition-all">
        <div className="flex flex-col items-center justify-center pt-5 pb-6">
          {loading ? (
            <div className="w-10 h-10 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin mb-3" />
          ) : (
            <UploadCloud className="w-10 h-10 text-gray-400 mb-3" />
          )}
          <p className="mb-2 text-sm text-gray-300 font-medium">
            <span className="font-semibold text-emerald-400">Click to upload</span> or drag and drop
          </p>
          <p className="text-xs text-gray-500">Must include: date, amount, category. Optional: merchant, description</p>
        </div>
        <input 
          type="file" 
          className="hidden" 
          accept=".csv" 
          onChange={handleFileUpload} 
          disabled={loading}
        />
      </label>
    </div>
  );
}
