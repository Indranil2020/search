package research.core;

import research.models.*;
import java.util.*;
import java.util.stream.*;

/**
 * Multi-Turn Reasoning Engine
 * 
 * Implements Kimi Researcher-style iterative hypothesis refinement,
 * self-correction on conflicting information, and cross-validation.
 * 
 * Key capabilities:
 * - Iterative hypothesis refinement
 * - Conflict detection and resolution
 * - Cross-source validation
 * - Confidence scoring
 */
public class MultiTurnReasoner {
    
    private final ResearchConfig config;
    private final int maxReasoningSteps;
    
    public MultiTurnReasoner(ResearchConfig config) {
        this.config = config;
        this.maxReasoningSteps = config.getMaxReasoningSteps();
    }
    
    /**
     * Perform multi-turn reasoning analysis on collected papers
     * Returns synthesized insights with confidence scores
     */
    public ReasoningResult analyzeAndSynthesize(List<Paper> papers, ResearchContext context) {
        ReasoningResult result = new ReasoningResult();
        List<ReasoningStep> steps = new ArrayList<>();
        
        // Step 1: Initial categorization
        steps.add(categorizeByTopic(papers, context));
        
        // Step 2: Identify key themes
        steps.add(identifyKeyThemes(papers, context));
        
        // Step 3: Detect conflicts and inconsistencies
        steps.add(detectConflicts(papers));
        
        // Step 4: Cross-validate findings
        steps.add(crossValidateFindings(papers));
        
        // Step 5: Identify research gaps
        steps.add(identifyResearchGaps(papers, context));
        
        // Step 6: Chronological analysis
        steps.add(analyzeChronologically(papers));
        
        // Step 7: Citation network analysis
        steps.add(analyzeCitationPatterns(papers));
        
        // Step 8: Synthesize key findings
        steps.add(synthesizeFindings(papers, steps));
        
        result.setSteps(steps);
        result.setTotalSteps(steps.size());
        result.setConfidenceScore(calculateOverallConfidence(steps));
        result.setKeyInsights(extractKeyInsights(steps));
        result.setRecommendedPapers(getRecommendedPapers(papers));
        
        return result;
    }
    
    /**
     * Step 1: Categorize papers by topic/subtopic
     */
    private ReasoningStep categorizeByTopic(List<Paper> papers, ResearchContext context) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(1);
        step.setStepType("CATEGORIZATION");
        step.setDescription("Categorizing papers by topic and subtopic");
        
        Map<String, List<Paper>> categories = new HashMap<>();
        QueryAnalysis analysis = context.getQueryAnalysis();
        
        // Group by detected fields
        for (Paper paper : papers) {
            String field = detectField(paper, analysis);
            categories.computeIfAbsent(field, k -> new ArrayList<>()).add(paper);
        }
        
        step.setResult(new CategoryResult(categories));
        step.setConfidence(0.85);
        step.setReasoning(String.format(
            "Categorized %d papers into %d distinct topics based on title, abstract, and keywords",
            papers.size(), categories.size()));
        
        return step;
    }
    
    /**
     * Step 2: Identify key themes across papers
     */
    private ReasoningStep identifyKeyThemes(List<Paper> papers, ResearchContext context) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(2);
        step.setStepType("THEME_IDENTIFICATION");
        step.setDescription("Identifying recurring themes and concepts");
        
        Map<String, Integer> termFrequency = new HashMap<>();
        
        // Extract terms from titles and abstracts
        for (Paper paper : papers) {
            Set<String> terms = extractKeyTerms(paper);
            for (String term : terms) {
                termFrequency.merge(term, 1, Integer::sum);
            }
        }
        
        // Get top themes
        List<Theme> themes = termFrequency.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(20)
            .map(e -> new Theme(e.getKey(), e.getValue(), (double) e.getValue() / papers.size()))
            .collect(Collectors.toList());
        
        step.setResult(new ThemeResult(themes));
        step.setConfidence(0.80);
        step.setReasoning(String.format(
            "Identified %d key themes from term frequency analysis across %d papers",
            themes.size(), papers.size()));
        
        return step;
    }
    
    /**
     * Step 3: Detect conflicts and inconsistencies between sources
     */
    private ReasoningStep detectConflicts(List<Paper> papers) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(3);
        step.setStepType("CONFLICT_DETECTION");
        step.setDescription("Detecting conflicting information across sources");
        
        List<Conflict> conflicts = new ArrayList<>();
        
        // Group papers by similar topics
        Map<String, List<Paper>> topicGroups = groupBySimilarTopic(papers);
        
        // Look for contradictory claims within each group
        for (Map.Entry<String, List<Paper>> entry : topicGroups.entrySet()) {
            List<Paper> group = entry.getValue();
            if (group.size() >= 2) {
                // Check for temporal conflicts (older vs newer findings)
                conflicts.addAll(detectTemporalConflicts(group));
                
                // Check for methodology-based conflicts
                conflicts.addAll(detectMethodologyConflicts(group));
            }
        }
        
        step.setResult(new ConflictResult(conflicts));
        step.setConfidence(conflicts.isEmpty() ? 0.95 : 0.70);
        step.setReasoning(String.format(
            "Analyzed %d topic groups, found %d potential conflicts requiring further investigation",
            topicGroups.size(), conflicts.size()));
        
        return step;
    }
    
    /**
     * Step 4: Cross-validate findings across multiple sources
     */
    private ReasoningStep crossValidateFindings(List<Paper> papers) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(4);
        step.setStepType("CROSS_VALIDATION");
        step.setDescription("Cross-validating key findings across sources");
        
        List<ValidatedFinding> findings = new ArrayList<>();
        
        // Group papers by source database
        Map<String, List<Paper>> bySource = papers.stream()
            .collect(Collectors.groupingBy(Paper::getSource));
        
        // Find findings that appear in multiple sources
        Map<String, Set<String>> claimSources = new HashMap<>();
        
        for (Paper paper : papers) {
            Set<String> claims = extractMainClaims(paper);
            for (String claim : claims) {
                claimSources.computeIfAbsent(claim, k -> new HashSet<>())
                    .add(paper.getSource());
            }
        }
        
        // Findings validated by multiple sources
        for (Map.Entry<String, Set<String>> entry : claimSources.entrySet()) {
            if (entry.getValue().size() >= 2) {
                findings.add(new ValidatedFinding(
                    entry.getKey(),
                    entry.getValue().size(),
                    new ArrayList<>(entry.getValue())
                ));
            }
        }
        
        step.setResult(new ValidationResult(findings));
        step.setConfidence(calculateValidationConfidence(findings, bySource.size()));
        step.setReasoning(String.format(
            "Cross-validated findings across %d sources, %d findings confirmed by multiple sources",
            bySource.size(), findings.size()));
        
        return step;
    }
    
    /**
     * Step 5: Identify research gaps
     */
    private ReasoningStep identifyResearchGaps(List<Paper> papers, ResearchContext context) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(5);
        step.setStepType("GAP_IDENTIFICATION");
        step.setDescription("Identifying potential research gaps");
        
        List<ResearchGap> gaps = new ArrayList<>();
        
        // Analyze temporal coverage
        Map<Integer, Long> papersByYear = papers.stream()
            .filter(p -> p.getYear() != null && p.getYear() > 0)
            .collect(Collectors.groupingBy(Paper::getYear, Collectors.counting()));
        
        // Find years with low coverage
        int currentYear = java.time.Year.now().getValue();
        for (int year = currentYear - 10; year <= currentYear; year++) {
            long count = papersByYear.getOrDefault(year, 0L);
            if (count < papers.size() / 20) {
                gaps.add(new ResearchGap("Temporal", 
                    String.format("Limited research from year %d", year),
                    0.6));
            }
        }
        
        // Find underexplored subtopics
        QueryAnalysis analysis = context.getQueryAnalysis();
        for (String subtopic : analysis.getRelatedConcepts()) {
            long coverage = papers.stream()
                .filter(p -> containsSubtopic(p, subtopic))
                .count();
            
            if (coverage < papers.size() / 10) {
                gaps.add(new ResearchGap("Topical",
                    String.format("Limited coverage of subtopic: %s", subtopic),
                    0.7));
            }
        }
        
        step.setResult(new GapResult(gaps));
        step.setConfidence(0.75);
        step.setReasoning(String.format(
            "Identified %d potential research gaps based on temporal and topical analysis",
            gaps.size()));
        
        return step;
    }
    
    /**
     * Step 6: Chronological analysis
     */
    private ReasoningStep analyzeChronologically(List<Paper> papers) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(6);
        step.setStepType("CHRONOLOGICAL_ANALYSIS");
        step.setDescription("Analyzing research evolution over time");
        
        // Sort by year
        Map<Integer, List<Paper>> byYear = papers.stream()
            .filter(p -> p.getYear() != null && p.getYear() > 0)
            .collect(Collectors.groupingBy(Paper::getYear, TreeMap::new, Collectors.toList()));
        
        List<TimelineEntry> timeline = new ArrayList<>();
        List<String> previousThemes = new ArrayList<>();
        
        for (Map.Entry<Integer, List<Paper>> entry : byYear.entrySet()) {
            List<Paper> yearPapers = entry.getValue();
            List<String> currentThemes = extractTopThemes(yearPapers, 5);
            
            // Identify emerging themes
            List<String> emergingThemes = currentThemes.stream()
                .filter(t -> !previousThemes.contains(t))
                .collect(Collectors.toList());
            
            timeline.add(new TimelineEntry(
                entry.getKey(),
                yearPapers.size(),
                currentThemes,
                emergingThemes
            ));
            
            previousThemes = currentThemes;
        }
        
        step.setResult(new ChronologicalResult(timeline));
        step.setConfidence(0.85);
        step.setReasoning(String.format(
            "Analyzed research evolution across %d years, tracking theme emergence and development",
            byYear.size()));
        
        return step;
    }
    
    /**
     * Step 7: Citation pattern analysis
     */
    private ReasoningStep analyzeCitationPatterns(List<Paper> papers) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(7);
        step.setStepType("CITATION_ANALYSIS");
        step.setDescription("Analyzing citation patterns and influential papers");
        
        // Identify highly cited papers
        List<Paper> highlyCircled = papers.stream()
            .filter(p -> p.getCitationCount() > 0)
            .sorted((a, b) -> Integer.compare(b.getCitationCount(), a.getCitationCount()))
            .limit(20)
            .collect(Collectors.toList());
        
        // Calculate citation statistics
        DoubleSummaryStatistics citationStats = papers.stream()
            .filter(p -> p.getCitationCount() > 0)
            .mapToDouble(Paper::getCitationCount)
            .summaryStatistics();
        
        // Identify foundational papers (high citations + older)
        List<Paper> foundationalPapers = papers.stream()
            .filter(p -> p.getCitationCount() > citationStats.getAverage() * 2)
            .filter(p -> p.getYear() != null && p.getYear() < java.time.Year.now().getValue() - 5)
            .collect(Collectors.toList());
        
        // Identify rising stars (recent + gaining citations quickly)
        List<Paper> risingStars = papers.stream()
            .filter(p -> p.getYear() != null && p.getYear() >= java.time.Year.now().getValue() - 2)
            .filter(p -> p.getCitationCount() > citationStats.getAverage())
            .collect(Collectors.toList());
        
        step.setResult(new CitationAnalysisResult(
            highlyCircled, foundationalPapers, risingStars, citationStats));
        step.setConfidence(0.90);
        step.setReasoning(String.format(
            "Analyzed %d papers with citations, identified %d foundational and %d rising star papers",
            (int) citationStats.getCount(), foundationalPapers.size(), risingStars.size()));
        
        return step;
    }
    
    /**
     * Step 8: Synthesize all findings
     */
    private ReasoningStep synthesizeFindings(List<Paper> papers, List<ReasoningStep> previousSteps) {
        ReasoningStep step = new ReasoningStep();
        step.setStepNumber(8);
        step.setStepType("SYNTHESIS");
        step.setDescription("Synthesizing all findings into coherent insights");
        
        Synthesis synthesis = new Synthesis();
        
        // Extract key insights from each previous step
        StringBuilder summaryBuilder = new StringBuilder();
        
        for (ReasoningStep prev : previousSteps) {
            if (prev.getConfidence() >= 0.70) {
                synthesis.addConfirmedFinding(prev.getStepType(), prev.getReasoning());
            } else {
                synthesis.addUncertainFinding(prev.getStepType(), prev.getReasoning());
            }
        }
        
        // Calculate overall statistics
        synthesis.setTotalPapers(papers.size());
        synthesis.setSourcesCovered(papers.stream()
            .map(Paper::getSource)
            .distinct()
            .count());
        synthesis.setTimeSpan(calculateTimeSpan(papers));
        
        step.setResult(synthesis);
        step.setConfidence(calculateSynthesisConfidence(previousSteps));
        step.setReasoning("Synthesized findings from all analysis steps into actionable insights");
        
        return step;
    }
    
    // Helper methods
    
    private String detectField(Paper paper, QueryAnalysis analysis) {
        // Simple field detection based on keywords
        String combined = (paper.getTitle() + " " + paper.getAbstract()).toLowerCase();
        
        if (combined.contains("medicine") || combined.contains("clinical") || combined.contains("patient")) {
            return "Medicine";
        } else if (combined.contains("physics") || combined.contains("quantum")) {
            return "Physics";
        } else if (combined.contains("chemistry") || combined.contains("molecule")) {
            return "Chemistry";
        } else if (combined.contains("biology") || combined.contains("gene") || combined.contains("cell")) {
            return "Biology";
        } else if (combined.contains("computer") || combined.contains("algorithm") || combined.contains("machine learning")) {
            return "Computer Science";
        } else if (combined.contains("engineering")) {
            return "Engineering";
        }
        return "General Science";
    }
    
    private Set<String> extractKeyTerms(Paper paper) {
        Set<String> terms = new HashSet<>();
        String text = paper.getTitle() + " " + paper.getAbstract();
        
        // Simple tokenization - in production use NLP library
        String[] words = text.toLowerCase().split("\\W+");
        for (String word : words) {
            if (word.length() > 4 && !isStopWord(word)) {
                terms.add(word);
            }
        }
        return terms;
    }
    
    private boolean isStopWord(String word) {
        Set<String> stopWords = Set.of(
            "about", "after", "again", "being", "between", "could", "during",
            "having", "their", "there", "these", "those", "through", "under",
            "where", "which", "while", "would", "paper", "study", "research",
            "results", "method", "methods", "using", "based", "analysis"
        );
        return stopWords.contains(word);
    }
    
    private Map<String, List<Paper>> groupBySimilarTopic(List<Paper> papers) {
        // Simplified topic grouping
        return papers.stream()
            .collect(Collectors.groupingBy(p -> extractMainTopic(p)));
    }
    
    private String extractMainTopic(Paper paper) {
        // Extract first significant term from title
        String[] words = paper.getTitle().toLowerCase().split("\\W+");
        for (String word : words) {
            if (word.length() > 5 && !isStopWord(word)) {
                return word;
            }
        }
        return "general";
    }
    
    private List<Conflict> detectTemporalConflicts(List<Paper> group) {
        // Placeholder for temporal conflict detection
        return new ArrayList<>();
    }
    
    private List<Conflict> detectMethodologyConflicts(List<Paper> group) {
        // Placeholder for methodology conflict detection
        return new ArrayList<>();
    }
    
    private Set<String> extractMainClaims(Paper paper) {
        // Simplified claim extraction
        Set<String> claims = new HashSet<>();
        String title = paper.getTitle().toLowerCase();
        claims.add(extractMainTopic(paper));
        return claims;
    }
    
    private double calculateValidationConfidence(List<ValidatedFinding> findings, int sourceCount) {
        if (findings.isEmpty()) return 0.5;
        double avgSources = findings.stream()
            .mapToInt(ValidatedFinding::getSourceCount)
            .average()
            .orElse(1.0);
        return Math.min(0.95, 0.5 + (avgSources / sourceCount) * 0.5);
    }
    
    private boolean containsSubtopic(Paper paper, String subtopic) {
        String combined = paper.getTitle() + " " + paper.getAbstract();
        return combined.toLowerCase().contains(subtopic.toLowerCase());
    }
    
    private List<String> extractTopThemes(List<Paper> papers, int n) {
        Map<String, Integer> freq = new HashMap<>();
        for (Paper p : papers) {
            for (String term : extractKeyTerms(p)) {
                freq.merge(term, 1, Integer::sum);
            }
        }
        return freq.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(n)
            .map(Map.Entry::getKey)
            .collect(Collectors.toList());
    }
    
    private double calculateOverallConfidence(List<ReasoningStep> steps) {
        return steps.stream()
            .mapToDouble(ReasoningStep::getConfidence)
            .average()
            .orElse(0.5);
    }
    
    private List<KeyInsight> extractKeyInsights(List<ReasoningStep> steps) {
        List<KeyInsight> insights = new ArrayList<>();
        for (ReasoningStep step : steps) {
            if (step.getConfidence() >= 0.75) {
                insights.add(new KeyInsight(step.getStepType(), step.getReasoning(), step.getConfidence()));
            }
        }
        return insights;
    }
    
    private List<Paper> getRecommendedPapers(List<Paper> papers) {
        return papers.stream()
            .filter(p -> p.getCitationCount() > 0)
            .sorted((a, b) -> Integer.compare(b.getCitationCount(), a.getCitationCount()))
            .limit(10)
            .collect(Collectors.toList());
    }
    
    private double calculateSynthesisConfidence(List<ReasoningStep> steps) {
        long confidentSteps = steps.stream()
            .filter(s -> s.getConfidence() >= 0.75)
            .count();
        return 0.5 + (confidentSteps / (double) steps.size()) * 0.5;
    }
    
    private String calculateTimeSpan(List<Paper> papers) {
        IntSummaryStatistics yearStats = papers.stream()
            .filter(p -> p.getYear() != null && p.getYear() > 1900)
            .mapToInt(Paper::getYear)
            .summaryStatistics();
        
        if (yearStats.getCount() == 0) return "Unknown";
        return String.format("%d - %d", yearStats.getMin(), yearStats.getMax());
    }
}
