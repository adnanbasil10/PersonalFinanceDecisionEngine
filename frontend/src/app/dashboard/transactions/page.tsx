"use client";

import { useState } from "react";
import Link from "next/link";
import ManualTransactionForm from "@/components/ui/ManualTransactionForm";
import CSVUploader from "@/components/ui/CSVUploader";
import Sidebar from "@/components/ui/Sidebar";
import { CheckCircle2, ArrowLeft } from "lucide-react";

export default function TransactionsPage() {
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 4000);
  };

  return (
    <div className="flex min-h-screen" style={{ background: "var(--color-background)" }}>
      <Sidebar activePage="transactions" />

      <main className="flex-1 p-6 lg:p-8 ml-0 lg:ml-64 overflow-auto">
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
          <header className="flex flex-col gap-4">
            <Link 
              href="/dashboard" 
              className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-emerald-400 transition-colors w-fit"
            >
              <ArrowLeft className="w-4 h-4" />
              Return to Dashboard
            </Link>
            
            <div>
              <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
                Data Center
              </h1>
              <p className="text-gray-400 mt-2">
                Add single transactions or bulk upload your bank statements.
              </p>
            </div>
          </header>

          {successMsg && (
            <div className="bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 p-4 rounded-xl flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5" />
              <p className="font-medium">{successMsg}</p>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            {/* Manual Form Pane */}
            <div className="bg-slate-900/50 border border-white/5 shadow-2xl shadow-emerald-900/5 rounded-2xl p-6 backdrop-blur-md">
              <h2 className="text-xl font-semibold text-white mb-4">Manual Entry</h2>
              <ManualTransactionForm onSuccess={() => handleSuccess("Transaction added successfully!")} />
            </div>

            {/* CSV Upload Pane */}
            <div className="bg-slate-900/50 border border-white/5 shadow-2xl shadow-cyan-900/5 rounded-2xl p-6 backdrop-blur-md flex flex-col">
              <h2 className="text-xl font-semibold text-white mb-2">Upload Bank Statement</h2>
              <p className="text-sm text-gray-500 mb-6">
                Save time by uploading your monthly expenses at once. Instantly syncs with the ML engine.
              </p>
              <div className="flex-1">
                <CSVUploader onSuccess={() => handleSuccess("Bulk CSV uploaded successfully! Models are updating.")} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
