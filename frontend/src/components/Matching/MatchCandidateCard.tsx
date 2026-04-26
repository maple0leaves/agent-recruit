import { Check, X } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import type { MatchResult } from "../../types/matching";

interface MatchCandidateCardProps {
  candidate: MatchResult;
  onApprove: () => void;
  onReject: () => void;
  isReviewed: boolean;
  decision?: "approved" | "rejected" | null;
}

export default function MatchCandidateCard({
  candidate,
  onApprove,
  onReject,
  isReviewed,
  decision,
}: MatchCandidateCardProps) {
  return (
    <Card
      className={`transition-all duration-300 ${
        isReviewed ? "opacity-60" : "hover:shadow-md"
      }`}
    >
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold">{candidate.candidate_name}</h3>
          {decision === "approved" && (
            <Badge variant="default" className="bg-green-500">
              已通过
            </Badge>
          )}
          {decision === "rejected" && (
            <Badge variant="destructive">已驳回</Badge>
          )}
        </div>
        <div className="flex items-center gap-1">
          <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {candidate.match_score}%
          </span>
          <span className="text-xs text-muted-foreground">匹配度</span>
        </div>
      </CardHeader>
      <CardContent className="pb-3">
        <div className="flex flex-wrap gap-2">
          {candidate.matched_skills.map((skill) => (
            <Badge
              key={`match-${skill}`}
              variant="default"
              className="flex items-center gap-1 bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-300"
            >
              <Check className="h-3 w-3" />
              {skill}
            </Badge>
          ))}
          {candidate.missing_skills.map((skill) => (
            <Badge
              key={`miss-${skill}`}
              variant="outline"
              className="flex items-center gap-1 border-red-300 text-red-600 dark:border-red-700 dark:text-red-400"
            >
              <X className="h-3 w-3" />
              {skill}
            </Badge>
          ))}
        </div>
        {candidate.recommendation && (
          <p className="mt-2 text-sm text-muted-foreground line-clamp-2">
            {candidate.recommendation}
          </p>
        )}
      </CardContent>
      <CardFooter className="flex justify-end gap-2 pt-0">
        <Button
          variant="outline"
          size="sm"
          onClick={onReject}
          disabled={isReviewed}
          className="border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-950"
        >
          驳回
        </Button>
        <Button
          variant="default"
          size="sm"
          onClick={onApprove}
          disabled={isReviewed}
          className="bg-green-600 hover:bg-green-700"
        >
          通过
        </Button>
      </CardFooter>
    </Card>
  );
}
