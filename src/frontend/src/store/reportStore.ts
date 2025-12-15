import { create } from 'zustand'

interface ReportStore {
  sessionId: string | null
  requirements: any | null
  costEstimate: any | null
  reportStructure: any | null
  reportData: any | null
  status: string
  
  setSessionId: (id: string) => void
  setRequirements: (req: any) => void
  setCostEstimate: (estimate: any) => void
  setReportStructure: (structure: any) => void
  setReportData: (data: any) => void
  setStatus: (status: string) => void
  reset: () => void
}

export const useReportStore = create<ReportStore>((set) => ({
  sessionId: null,
  requirements: null,
  costEstimate: null,
  reportStructure: null,
  reportData: null,
  status: 'idle',
  
  setSessionId: (id) => set({ sessionId: id }),
  setRequirements: (req) => set({ requirements: req }),
  setCostEstimate: (estimate) => set({ costEstimate: estimate }),
  setReportStructure: (structure) => set({ reportStructure: structure }),
  setReportData: (data) => set({ reportData: data }),
  setStatus: (status) => set({ status }),
  reset: () => set({
    sessionId: null,
    requirements: null,
    costEstimate: null,
    reportStructure: null,
    reportData: null,
    status: 'idle',
  }),
}))

