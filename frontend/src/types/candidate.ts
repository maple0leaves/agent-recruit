export type CandidateStatus = "new" | "screening" | "interview" | "hired" | "rejected";

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone: string;
  skills: string;
  education: string;
  experience: string;
  status: CandidateStatus;
  resume_file_path: string;
  status_note: string;
  parsed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CandidateListResponse {
  items: Candidate[];
  total: number;
  page: number;
  page_size: number;
}

export interface CandidateUpdate {
  name?: string;
  email?: string;
  phone?: string;
  skills?: string;
  education?: string;
  experience?: string;
}

export interface CandidateUploadResponse extends Candidate {
  warnings?: string[];
}
