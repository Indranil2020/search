package research.models;

import java.util.*;
import java.time.Instant;

/**
 * Paper - Core data model for academic papers
 */
public class Paper {
    
    private String id;
    private String title;
    private List<String> authors = new ArrayList<>();
    private Integer year;
    private String abstractText;
    private String journal;
    private String publisher;
    private String doi;
    private String pmid;
    private String arxivId;
    private String source;
    private int citationCount;
    private AccessType accessType = AccessType.UNKNOWN;
    private String pdfUrl;
    private Map<String, String> urls = new HashMap<>();
    private double relevanceScore;
    private List<String> keywords = new ArrayList<>();
    
    // Getters and setters
    
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    
    public List<String> getAuthors() { return authors; }
    public void setAuthors(List<String> authors) { this.authors = authors; }
    
    public Integer getYear() { return year; }
    public void setYear(Integer year) { this.year = year; }
    
    public String getAbstract() { return abstractText; }
    public void setAbstract(String abstractText) { this.abstractText = abstractText; }
    
    public String getJournal() { return journal; }
    public void setJournal(String journal) { this.journal = journal; }
    
    public String getPublisher() { return publisher; }
    public void setPublisher(String publisher) { this.publisher = publisher; }
    
    public String getDoi() { return doi; }
    public void setDoi(String doi) { this.doi = doi; }
    
    public String getPmid() { return pmid; }
    public void setPmid(String pmid) { this.pmid = pmid; }
    
    public String getArxivId() { return arxivId; }
    public void setArxivId(String arxivId) { this.arxivId = arxivId; }
    
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    
    public int getCitationCount() { return citationCount; }
    public void setCitationCount(int citationCount) { this.citationCount = citationCount; }
    
    public AccessType getAccessType() { return accessType; }
    public void setAccessType(AccessType accessType) { this.accessType = accessType; }
    
    public String getPdfUrl() { return pdfUrl; }
    public void setPdfUrl(String pdfUrl) { this.pdfUrl = pdfUrl; }
    
    public Map<String, String> getUrls() { return urls; }
    public void setUrls(Map<String, String> urls) { this.urls = urls; }
    
    public double getRelevanceScore() { return relevanceScore; }
    public void setRelevanceScore(double relevanceScore) { this.relevanceScore = relevanceScore; }
    
    public List<String> getKeywords() { return keywords; }
    public void setKeywords(List<String> keywords) { this.keywords = keywords; }
    
    // Convenience methods
    
    public String getUniqueId() {
        if (doi != null && !doi.isEmpty()) return "doi:" + doi;
        if (pmid != null && !pmid.isEmpty()) return "pmid:" + pmid;
        if (arxivId != null && !arxivId.isEmpty()) return "arxiv:" + arxivId;
        return "title:" + title.toLowerCase().hashCode();
    }
    
    public void addUrl(String type, String url) {
        urls.put(type, url);
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Paper paper = (Paper) o;
        return Objects.equals(getUniqueId(), paper.getUniqueId());
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(getUniqueId());
    }
}

/**
 * Access type enumeration
 */
enum AccessType {
    OPEN_ACCESS,
    GREEN,
    GOLD,
    BRONZE,
    HYBRID,
    PAYWALLED,
    SCIHUB,
    UNKNOWN
}

/**
 * Research result - Complete result of a research query
 */
class ResearchResult {
    
    private List<Paper> papers;
    private ReasoningResult reasoning;
    private ResearchStatistics stats;
    
    public ResearchResult(List<Paper> papers, ReasoningResult reasoning, ResearchStatistics stats) {
        this.papers = papers;
        this.reasoning = reasoning;
        this.stats = stats;
    }
    
    public List<Paper> getPapers() { return papers; }
    public ReasoningResult getReasoning() { return reasoning; }
    public ResearchStatistics getStats() { return stats; }
}

/**
 * Research statistics
 */
class ResearchStatistics {
    
    private Instant startTime;
    private Instant endTime;
    private int totalRawPapers;
    private int totalUniquePapers;
    private int duplicatesRemoved;
    private int sourcesQueried;
    private Map<String, Integer> phaseResults = new HashMap<>();
    private Map<String, Integer> papersBySource = new HashMap<>();
    
    public void reset() {
        startTime = null;
        endTime = null;
        totalRawPapers = 0;
        totalUniquePapers = 0;
        duplicatesRemoved = 0;
        sourcesQueried = 0;
        phaseResults.clear();
        papersBySource.clear();
    }
    
    public void setStartTime(Instant startTime) { this.startTime = startTime; }
    public void setEndTime(Instant endTime) { this.endTime = endTime; }
    public void setTotalUniquePapers(int count) { this.totalUniquePapers = count; }
    public void setDuplicatesRemoved(int count) { this.duplicatesRemoved = count; }
    
    public void addPhaseResults(String phase, int count) {
        phaseResults.put(phase, count);
        totalRawPapers += count;
    }
    
    public void incrementSourcesQueried() { sourcesQueried++; }
    
    public int getTotalRawPapers() { return totalRawPapers; }
    public int getSourcesQueried() { return sourcesQueried; }
    
    public long getDurationSeconds() {
        if (startTime == null || endTime == null) return 0;
        return java.time.Duration.between(startTime, endTime).getSeconds();
    }
}

/**
 * Research context - Holds query analysis and context
 */
class ResearchContext {
    
    private String originalQuery;
    private QueryAnalysis queryAnalysis;
    private Map<String, Object> metadata = new HashMap<>();
    
    public ResearchContext(String query) {
        this.originalQuery = query;
    }
    
    public String getOriginalQuery() { return originalQuery; }
    public QueryAnalysis getQueryAnalysis() { return queryAnalysis; }
    public void setQueryAnalysis(QueryAnalysis analysis) { this.queryAnalysis = analysis; }
}

/**
 * Query analysis result
 */
class QueryAnalysis {
    
    private String originalQuery;
    private List<String> keywords = new ArrayList<>();
    private List<String> relatedConcepts = new ArrayList<>();
    private String detectedField;
    private boolean isReviewQuery;
    private boolean isMethodologyQuery;
    
    public String getOriginalQuery() { return originalQuery; }
    public void setOriginalQuery(String originalQuery) { this.originalQuery = originalQuery; }
    
    public List<String> getKeywords() { return keywords; }
    public void setKeywords(List<String> keywords) { this.keywords = keywords; }
    
    public List<String> getRelatedConcepts() { return relatedConcepts; }
    public void setRelatedConcepts(List<String> concepts) { this.relatedConcepts = concepts; }
    
    public String getDetectedField() { return detectedField; }
    public void setDetectedField(String field) { this.detectedField = field; }
    
    public boolean isReviewQuery() { return isReviewQuery; }
    public void setReviewQuery(boolean reviewQuery) { isReviewQuery = reviewQuery; }
    
    public boolean isMethodologyQuery() { return isMethodologyQuery; }
    public void setMethodologyQuery(boolean methodologyQuery) { isMethodologyQuery = methodologyQuery; }
}

/**
 * Progress update for UI callbacks
 */
class ProgressUpdate {
    
    private String stage;
    private String message;
    private String status;
    private Instant timestamp;
    
    public ProgressUpdate(String stage, String message, String status, Instant timestamp) {
        this.stage = stage;
        this.message = message;
        this.status = status;
        this.timestamp = timestamp;
    }
    
    public String getStage() { return stage; }
    public String getMessage() { return message; }
    public String getStatus() { return status; }
    public Instant getTimestamp() { return timestamp; }
}

/**
 * Reasoning result from multi-turn analysis
 */
class ReasoningResult {
    
    private List<ReasoningStep> steps = new ArrayList<>();
    private int totalSteps;
    private double confidenceScore;
    private List<KeyInsight> keyInsights = new ArrayList<>();
    private List<Paper> recommendedPapers = new ArrayList<>();
    
    public List<ReasoningStep> getSteps() { return steps; }
    public void setSteps(List<ReasoningStep> steps) { this.steps = steps; }
    
    public int getTotalSteps() { return totalSteps; }
    public void setTotalSteps(int totalSteps) { this.totalSteps = totalSteps; }
    
    public double getConfidenceScore() { return confidenceScore; }
    public void setConfidenceScore(double confidenceScore) { this.confidenceScore = confidenceScore; }
    
    public List<KeyInsight> getKeyInsights() { return keyInsights; }
    public void setKeyInsights(List<KeyInsight> keyInsights) { this.keyInsights = keyInsights; }
    
    public List<Paper> getRecommendedPapers() { return recommendedPapers; }
    public void setRecommendedPapers(List<Paper> papers) { this.recommendedPapers = papers; }
}

/**
 * Individual reasoning step
 */
class ReasoningStep {
    
    private int stepNumber;
    private String stepType;
    private String description;
    private Object result;
    private double confidence;
    private String reasoning;
    
    public int getStepNumber() { return stepNumber; }
    public void setStepNumber(int stepNumber) { this.stepNumber = stepNumber; }
    
    public String getStepType() { return stepType; }
    public void setStepType(String stepType) { this.stepType = stepType; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public Object getResult() { return result; }
    public void setResult(Object result) { this.result = result; }
    
    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }
    
    public String getReasoning() { return reasoning; }
    public void setReasoning(String reasoning) { this.reasoning = reasoning; }
}

/**
 * Key insight from analysis
 */
class KeyInsight {
    
    private String type;
    private String content;
    private double confidence;
    
    public KeyInsight(String type, String content, double confidence) {
        this.type = type;
        this.content = content;
        this.confidence = confidence;
    }
    
    public String getType() { return type; }
    public String getContent() { return content; }
    public double getConfidence() { return confidence; }
}

// Additional result types for reasoning steps

class CategoryResult {
    private Map<String, List<Paper>> categories;
    public CategoryResult(Map<String, List<Paper>> categories) { this.categories = categories; }
    public Map<String, List<Paper>> getCategories() { return categories; }
}

class Theme {
    private String name;
    private int count;
    private double frequency;
    public Theme(String name, int count, double frequency) {
        this.name = name; this.count = count; this.frequency = frequency;
    }
}

class ThemeResult {
    private List<Theme> themes;
    public ThemeResult(List<Theme> themes) { this.themes = themes; }
}

class Conflict {
    private Paper paper1;
    private Paper paper2;
    private String conflictType;
    private String description;
}

class ConflictResult {
    private List<Conflict> conflicts;
    public ConflictResult(List<Conflict> conflicts) { this.conflicts = conflicts; }
}

class ValidatedFinding {
    private String finding;
    private int sourceCount;
    private List<String> sources;
    public ValidatedFinding(String finding, int sourceCount, List<String> sources) {
        this.finding = finding; this.sourceCount = sourceCount; this.sources = sources;
    }
    public int getSourceCount() { return sourceCount; }
}

class ValidationResult {
    private List<ValidatedFinding> findings;
    public ValidationResult(List<ValidatedFinding> findings) { this.findings = findings; }
}

class ResearchGap {
    private String type;
    private String description;
    private double importance;
    public ResearchGap(String type, String description, double importance) {
        this.type = type; this.description = description; this.importance = importance;
    }
}

class GapResult {
    private List<ResearchGap> gaps;
    public GapResult(List<ResearchGap> gaps) { this.gaps = gaps; }
}

class TimelineEntry {
    private int year;
    private int paperCount;
    private List<String> themes;
    private List<String> emergingThemes;
    public TimelineEntry(int year, int paperCount, List<String> themes, List<String> emergingThemes) {
        this.year = year; this.paperCount = paperCount;
        this.themes = themes; this.emergingThemes = emergingThemes;
    }
}

class ChronologicalResult {
    private List<TimelineEntry> timeline;
    public ChronologicalResult(List<TimelineEntry> timeline) { this.timeline = timeline; }
}

class CitationAnalysisResult {
    private List<Paper> highlyCited;
    private List<Paper> foundational;
    private List<Paper> risingStars;
    private DoubleSummaryStatistics stats;
    public CitationAnalysisResult(List<Paper> highlyCited, List<Paper> foundational,
                                    List<Paper> risingStars, DoubleSummaryStatistics stats) {
        this.highlyCited = highlyCited; this.foundational = foundational;
        this.risingStars = risingStars; this.stats = stats;
    }
}

class Synthesis {
    private int totalPapers;
    private long sourcesCovered;
    private String timeSpan;
    private Map<String, String> confirmedFindings = new HashMap<>();
    private Map<String, String> uncertainFindings = new HashMap<>();
    
    public void setTotalPapers(int count) { this.totalPapers = count; }
    public void setSourcesCovered(long count) { this.sourcesCovered = count; }
    public void setTimeSpan(String span) { this.timeSpan = span; }
    public void addConfirmedFinding(String type, String finding) { confirmedFindings.put(type, finding); }
    public void addUncertainFinding(String type, String finding) { uncertainFindings.put(type, finding); }
}

class OpenAccessResult {
    private boolean hasOpenAccess;
    private String pdfUrl;
    private AccessType accessType;
    
    public OpenAccessResult(boolean hasOpenAccess, String pdfUrl, AccessType accessType) {
        this.hasOpenAccess = hasOpenAccess;
        this.pdfUrl = pdfUrl;
        this.accessType = accessType;
    }
    
    public boolean hasOpenAccess() { return hasOpenAccess; }
    public String getPdfUrl() { return pdfUrl; }
    public AccessType getAccessType() { return accessType; }
}
