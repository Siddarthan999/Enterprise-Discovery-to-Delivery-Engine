import { Rocket } from "lucide-react";

export default function DeliveryHeader() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-5 shadow-2xl shadow-cyan-950/20">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-[#c90c61]/10 p-2 text-[#c90c61]">
          <Rocket size={22} />
        </div>

        <div>
          <h1 className="text-2xl font-semibold text-white">
            Delivery Workspace
          </h1>

          <p className="mt-1 text-sm text-zinc-400">
            Generate execution artifacts from approved Statements of Work.
          </p>
        </div>
      </div>
    </div>
  );
}