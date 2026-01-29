"use client";

import { use } from "react";
import { ProcessingView } from "@/components/dashboard/processing-view";

interface ProcessingPageProps {
  params: Promise<{ id: string }>;
}

export default function ProcessingPage({ params }: ProcessingPageProps) {
  const resolvedParams = use(params);
  
  return (
    <div className="p-8">
      <ProcessingView generationId={resolvedParams.id} />
    </div>
  );
}
