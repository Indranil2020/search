package research.core;

import research.adapters.*;
import research.processors.*;
import research.models.*;

import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;
import java.time.Instant;
import java.util.function.Consumer;

/**
 * Ultra Research System - Main Orchestrator
 * 
 * Kimi Researcher-class comprehensive scientific literature discovery engine.
 * Coordinates 50+ data sources for exhaustive literature search.
 * 
 * @author Ultra Research System
 * @version 1.0.0
 */
public class ResearchOrchestrator {
    
    private final SourceRegistry sourceRegistry;
    private final Deduplicator deduplicator;
    private final RelevanceRanker ranker;
    private final CitationNetworkBuilder citationBuilder;
    private final QueryExpander queryExpander;
    private final MultiTurnReasoner reasoner;
    private final ExecutorService executorService;
    private final ResearchConfig config;
    
    // Statistics tracking
    private final ResearchStatistics stats;
    
    public ResearchOrchestrator() {
        this(ResearchConfig.defaultConfig());
    }
    
    public ResearchOrchestrator(ResearchConfig config) {
        this.config = config;
        this.sourceRegistry = new SourceRegistry(config);
        this.deduplicator = new Deduplicator();
        this.ranker = new RelevanceRanker();
        this.citationBuilder = new CitationNetworkBuilder();
        this.queryExpander = new QueryExpander();
        this.reasoner = new MultiTurnReasoner(config);
        this.executorService = Executors.newFixedThreadPool(config.getThreadPoolSize());
        this.stats = new ResearchStatistics();
    }
    
    /**
     * Execute comprehensive multi-phase research
     * Mirrors Kimi Researcher's approach: 23+ reasoning steps, 200+ URLs
     */
    public ResearchResult executeComprehensiveSearch(String query) {
        return executeComprehensiveSearch(query, null);
    }
    
    public ResearchResult executeComprehensiveSearch(String query, Consumer<ProgressUpdate> progressCallback) {
        stats.reset();
        stats.setStartTime(Instant.now());
        
        List<Paper> allPapers = new CopyOnWriteArrayList<>();
        ResearchContext context = new ResearchContext(query);
        
        // Phase 1: Query Analysis and Expansion
        reportProgress(progressCallback, "PHASE_1", "Analyzing query and generating variations", "RUNNING");
        QueryAnalysis analysis = queryExpander.analyze(query);
        List<String> queryVariations = queryExpander.generateVariations(query, analysis);
        context.setQueryAnalysis(analysis);
        reportProgress(progressCallback, "PHASE_1", 
            String.format("Generated %d query variations", queryVariations.size()), "COMPLETE");
        
        // Phase 2: Priority Academic Databases (FREE)
        reportProgress(progressCallback, "PHASE_2", "Searching priority academic databases", "RUNNING");
        List<Paper> phase2Papers = searchPriorityDatabases(query, queryVariations, progressCallback);
        allPapers.addAll(phase2Papers);
        stats.addPhaseResults("Priority Databases", phase2Papers.size());
        
        // Phase 3: Google Scholar (Critical for completeness)
        reportProgress(progressCallback, "PHASE_3", "Searching Google Scholar", "RUNNING");
        List<Paper> scholarPapers = searchGoogleScholar(query, progressCallback);
        allPapers.addAll(scholarPapers);
        stats.addPhaseResults("Google Scholar", scholarPapers.size());
        
        // Phase 4: Citation Databases
        reportProgress(progressCallback, "PHASE_4", "Searching citation databases", "RUNNING");
        List<Paper> citationPapers = searchCitationDatabases(query, progressCallback);
        allPapers.addAll(citationPapers);
        stats.addPhaseResults("Citation Databases", citationPapers.size());
        
        // Phase 5: All Publishers (50+)
        reportProgress(progressCallback, "PHASE_5", "Searching all major publishers", "RUNNING");
        List<Paper> publisherPapers = searchAllPublishers(query, progressCallback);
        allPapers.addAll(publisherPapers);
        stats.addPhaseResults("Publishers", publisherPapers.size());
        
        // Phase 6: Preprint Servers
        reportProgress(progressCallback, "PHASE_6", "Searching preprint servers", "RUNNING");
        List<Paper> preprintPapers = searchPreprintServers(query, progressCallback);
        allPapers.addAll(preprintPapers);
        stats.addPhaseResults("Preprints", preprintPapers.size());
        
        // Phase 7: Citation Network Expansion (Kimi-style deep exploration)
        reportProgress(progressCallback, "PHASE_7", "Expanding citation networks", "RUNNING");
        List<Paper> citedPapers = expandCitationNetwork(allPapers, progressCallback);
        allPapers.addAll(citedPapers);
        stats.addPhaseResults("Citation Expansion", citedPapers.size());
        
        // Phase 8: Alternative Search (DuckDuckGo, Brave)
        reportProgress(progressCallback, "PHASE_8", "Searching alternative engines", "RUNNING");
        List<Paper> altSearchPapers = searchAlternativeEngines(query, progressCallback);
        allPapers.addAll(altSearchPapers);
        stats.addPhaseResults("Alternative Search", altSearchPapers.size());
        
        // Phase 9: Query Variation Deep Dive
        reportProgress(progressCallback, "PHASE_9", "Deep diving query variations", "RUNNING");
        for (String variation : queryVariations.subList(0, Math.min(5, queryVariations.size()))) {
            List<Paper> variationPapers = searchSemanticScholar(variation);
            allPapers.addAll(variationPapers);
        }
        stats.addPhaseResults("Query Variations", allPapers.size() - stats.getTotalRawPapers());
        
        // Phase 10: Deduplication
        reportProgress(progressCallback, "PHASE_10", "Deduplicating results", "RUNNING");
        int rawCount = allPapers.size();
        List<Paper> uniquePapers = deduplicator.deduplicate(allPapers);
        stats.setDuplicatesRemoved(rawCount - uniquePapers.size());
        reportProgress(progressCallback, "PHASE_10", 
            String.format("Removed %d duplicates", rawCount - uniquePapers.size()), "COMPLETE");
        
        // Phase 11: Relevance Ranking
        reportProgress(progressCallback, "PHASE_11", "Ranking by relevance", "RUNNING");
        List<Paper> rankedPapers = ranker.rankByRelevance(uniquePapers, query, analysis);
        
        // Phase 12: Open Access Resolution
        reportProgress(progressCallback, "PHASE_12", "Resolving open access links", "RUNNING");
        enrichWithOpenAccessLinks(rankedPapers, progressCallback);
        
        // Phase 13: Multi-Turn Reasoning Analysis (Kimi-style)
        reportProgress(progressCallback, "PHASE_13", "Performing multi-turn reasoning analysis", "RUNNING");
        ReasoningResult reasoning = reasoner.analyzeAndSynthesize(rankedPapers, context);
        
        stats.setEndTime(Instant.now());
        stats.setTotalUniquePapers(rankedPapers.size());
        
        reportProgress(progressCallback, "COMPLETE", 
            String.format("Found %d unique papers from %d sources", 
                rankedPapers.size(), stats.getSourcesQueried()), "COMPLETE");
        
        return new ResearchResult(rankedPapers, reasoning, stats);
    }
    
    /**
     * Phase 2: Search priority academic databases in parallel
     */
    private List<Paper> searchPriorityDatabases(String query, List<String> variations, 
                                                  Consumer<ProgressUpdate> callback) {
        List<Callable<List<Paper>>> tasks = new ArrayList<>();
        
        // PubMed
        tasks.add(() -> {
            reportProgress(callback, "PubMed", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("pubmed").search(query);
            reportProgress(callback, "PubMed", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // arXiv
        tasks.add(() -> {
            reportProgress(callback, "arXiv", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("arxiv").search(query);
            reportProgress(callback, "arXiv", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // Semantic Scholar
        tasks.add(() -> {
            reportProgress(callback, "Semantic Scholar", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("semantic_scholar").search(query);
            reportProgress(callback, "Semantic Scholar", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // CrossRef
        tasks.add(() -> {
            reportProgress(callback, "CrossRef", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("crossref").search(query);
            reportProgress(callback, "CrossRef", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // BASE
        tasks.add(() -> {
            reportProgress(callback, "BASE", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("base").search(query);
            reportProgress(callback, "BASE", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // CORE
        tasks.add(() -> {
            reportProgress(callback, "CORE", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("core").search(query);
            reportProgress(callback, "CORE", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // OpenAlex
        tasks.add(() -> {
            reportProgress(callback, "OpenAlex", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("openalex").search(query);
            reportProgress(callback, "OpenAlex", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // Europe PMC
        tasks.add(() -> {
            reportProgress(callback, "Europe PMC", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("europepmc").search(query);
            reportProgress(callback, "Europe PMC", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        return executeParallelSearches(tasks);
    }
    
    /**
     * Phase 3: Google Scholar search via scholarly Python bridge
     */
    private List<Paper> searchGoogleScholar(String query, Consumer<ProgressUpdate> callback) {
        reportProgress(callback, "Google Scholar", "Searching via scholarly...", "RUNNING");
        List<Paper> papers = sourceRegistry.getAdapter("google_scholar").search(query);
        reportProgress(callback, "Google Scholar", String.format("Found %d papers", papers.size()), "COMPLETE");
        stats.incrementSourcesQueried();
        return papers;
    }
    
    /**
     * Phase 4: Search citation databases
     */
    private List<Paper> searchCitationDatabases(String query, Consumer<ProgressUpdate> callback) {
        List<Callable<List<Paper>>> tasks = new ArrayList<>();
        
        // OpenCitations (FREE)
        tasks.add(() -> {
            reportProgress(callback, "OpenCitations", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("opencitations").search(query);
            reportProgress(callback, "OpenCitations", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // Dimensions (FREE tier)
        tasks.add(() -> {
            reportProgress(callback, "Dimensions", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("dimensions").search(query);
            reportProgress(callback, "Dimensions", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // Lens.org (FREE)
        tasks.add(() -> {
            reportProgress(callback, "Lens.org", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("lens").search(query);
            reportProgress(callback, "Lens.org", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // Scopus (if API key available)
        if (config.hasApiKey("scopus")) {
            tasks.add(() -> {
                reportProgress(callback, "Scopus", "Searching...", "RUNNING");
                List<Paper> papers = sourceRegistry.getAdapter("scopus").search(query);
                reportProgress(callback, "Scopus", String.format("Found %d papers", papers.size()), "COMPLETE");
                return papers;
            });
        }
        
        // Web of Science (if API key available)
        if (config.hasApiKey("wos")) {
            tasks.add(() -> {
                reportProgress(callback, "Web of Science", "Searching...", "RUNNING");
                List<Paper> papers = sourceRegistry.getAdapter("wos").search(query);
                reportProgress(callback, "Web of Science", String.format("Found %d papers", papers.size()), "COMPLETE");
                return papers;
            });
        }
        
        return executeParallelSearches(tasks);
    }
    
    /**
     * Phase 5: Search ALL major publishers (50+)
     */
    private List<Paper> searchAllPublishers(String query, Consumer<ProgressUpdate> callback) {
        List<Callable<List<Paper>>> tasks = new ArrayList<>();
        
        // Complete list of publishers to search
        String[] publishers = {
            // Tier 1: Major Commercial Publishers
            "springer_nature", "elsevier", "wiley", "ieee", "taylor_francis", "sage",
            
            // Tier 2: Scientific Society Publishers
            "acs", "aps", "iop", "rsc", "aaas_science", "asm", "aip",
            
            // Tier 3: University Presses
            "cambridge", "oxford", "mit_press", "princeton", "yale", "harvard",
            "chicago", "stanford", "duke", "jhu", "columbia", "cornell",
            "michigan", "minnesota", "california", "toronto", "penn",
            "nyu", "melbourne", "unsw",
            
            // Tier 4: Open Access Publishers
            "frontiers", "mdpi", "plos", "bmc", "hindawi", "peerj",
            
            // Tier 5: Other Major Publishers
            "palgrave", "edward_elgar", "de_gruyter", "brill", "emerald",
            "karger", "thieme", "lippincott", "wolters_kluwer",
            
            // Tier 6: Regional/Specialized
            "copernicus", "ingenta", "jstor", "project_muse"
        };
        
        for (String publisher : publishers) {
            final String pub = publisher;
            tasks.add(() -> {
                reportProgress(callback, pub, "Searching...", "RUNNING");
                // Most publishers are searched via CrossRef filtered by publisher name
                List<Paper> papers = sourceRegistry.getAdapter("crossref")
                    .searchByPublisher(query, pub);
                reportProgress(callback, pub, String.format("Found %d papers", papers.size()), "COMPLETE");
                return papers;
            });
        }
        
        // Also search publishers with direct APIs
        if (config.hasApiKey("springer")) {
            tasks.add(() -> {
                reportProgress(callback, "Springer API", "Searching directly...", "RUNNING");
                List<Paper> papers = sourceRegistry.getAdapter("springer").search(query);
                reportProgress(callback, "Springer API", String.format("Found %d papers", papers.size()), "COMPLETE");
                return papers;
            });
        }
        
        if (config.hasApiKey("ieee")) {
            tasks.add(() -> {
                reportProgress(callback, "IEEE API", "Searching directly...", "RUNNING");
                List<Paper> papers = sourceRegistry.getAdapter("ieee").search(query);
                reportProgress(callback, "IEEE API", String.format("Found %d papers", papers.size()), "COMPLETE");
                return papers;
            });
        }
        
        return executeParallelSearches(tasks);
    }
    
    /**
     * Phase 6: Search all preprint servers
     */
    private List<Paper> searchPreprintServers(String query, Consumer<ProgressUpdate> callback) {
        List<Callable<List<Paper>>> tasks = new ArrayList<>();
        
        String[] preprintServers = {
            "biorxiv", "medrxiv", "chemrxiv", "ssrn", "osf_preprints",
            "eartharxiv", "psyarxiv", "socarxiv", "engrxiv", "preprints_org",
            "authorea", "research_square", "techrxiv"
        };
        
        for (String server : preprintServers) {
            final String srv = server;
            tasks.add(() -> {
                reportProgress(callback, srv, "Searching...", "RUNNING");
                List<Paper> papers = sourceRegistry.getAdapter(srv).search(query);
                reportProgress(callback, srv, String.format("Found %d papers", papers.size()), "COMPLETE");
                return papers;
            });
        }
        
        return executeParallelSearches(tasks);
    }
    
    /**
     * Phase 7: Expand citation networks (Kimi-style deep exploration)
     */
    private List<Paper> expandCitationNetwork(List<Paper> papers, Consumer<ProgressUpdate> callback) {
        // Get top-cited papers for network expansion
        List<Paper> topPapers = papers.stream()
            .sorted((a, b) -> Integer.compare(b.getCitationCount(), a.getCitationCount()))
            .limit(config.getCitationExpansionLimit())
            .collect(Collectors.toList());
        
        List<Paper> networkPapers = new ArrayList<>();
        
        for (Paper paper : topPapers) {
            if (paper.getDoi() != null) {
                // Get papers that cite this paper
                List<Paper> citingPapers = citationBuilder.getCitingPapers(paper.getDoi());
                networkPapers.addAll(citingPapers);
                
                // Get papers that this paper cites
                List<Paper> citedPapers = citationBuilder.getCitedPapers(paper.getDoi());
                networkPapers.addAll(citedPapers);
            }
        }
        
        reportProgress(callback, "Citation Network", 
            String.format("Expanded network with %d papers", networkPapers.size()), "COMPLETE");
        
        return networkPapers;
    }
    
    /**
     * Phase 8: Alternative search engines (DuckDuckGo, Brave)
     */
    private List<Paper> searchAlternativeEngines(String query, Consumer<ProgressUpdate> callback) {
        List<Callable<List<Paper>>> tasks = new ArrayList<>();
        
        // DuckDuckGo
        tasks.add(() -> {
            reportProgress(callback, "DuckDuckGo", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("duckduckgo").search(query + " research paper pdf");
            reportProgress(callback, "DuckDuckGo", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // Brave Search
        tasks.add(() -> {
            reportProgress(callback, "Brave Search", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("brave").search(query + " academic paper");
            reportProgress(callback, "Brave Search", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        // Bing Academic
        tasks.add(() -> {
            reportProgress(callback, "Bing Academic", "Searching...", "RUNNING");
            List<Paper> papers = sourceRegistry.getAdapter("bing").search(query);
            reportProgress(callback, "Bing Academic", String.format("Found %d papers", papers.size()), "COMPLETE");
            return papers;
        });
        
        return executeParallelSearches(tasks);
    }
    
    /**
     * Search Semantic Scholar directly
     */
    private List<Paper> searchSemanticScholar(String query) {
        return sourceRegistry.getAdapter("semantic_scholar").search(query);
    }
    
    /**
     * Enrich papers with open access links (Unpaywall, Sci-Hub)
     */
    private void enrichWithOpenAccessLinks(List<Paper> papers, Consumer<ProgressUpdate> callback) {
        FullTextResolver resolver = new FullTextResolver(config);
        
        int resolved = 0;
        for (Paper paper : papers) {
            if (paper.getDoi() != null && paper.getPdfUrl() == null) {
                OpenAccessResult result = resolver.findFullText(paper.getDoi());
                if (result.hasOpenAccess()) {
                    paper.setPdfUrl(result.getPdfUrl());
                    paper.setAccessType(result.getAccessType());
                    resolved++;
                }
            }
        }
        
        reportProgress(callback, "Open Access", 
            String.format("Resolved %d open access links", resolved), "COMPLETE");
    }
    
    /**
     * Execute search tasks in parallel
     */
    private List<Paper> executeParallelSearches(List<Callable<List<Paper>>> tasks) {
        List<Paper> results = new ArrayList<>();
        
        List<Future<List<Paper>>> futures = tasks.stream()
            .map(executorService::submit)
            .collect(Collectors.toList());
        
        for (Future<List<Paper>> future : futures) {
            List<Paper> papers = safeGet(future);
            if (papers != null) {
                results.addAll(papers);
                stats.incrementSourcesQueried();
            }
        }
        
        return results;
    }
    
    /**
     * Safely get result from Future without throwing checked exceptions
     */
    private <T> T safeGet(Future<T> future) {
        return FutureUtils.getQuietly(future, config.getSearchTimeout());
    }
    
    private void reportProgress(Consumer<ProgressUpdate> callback, String stage, 
                                  String message, String status) {
        if (callback != null) {
            callback.accept(new ProgressUpdate(stage, message, status, Instant.now()));
        }
    }
    
    public void shutdown() {
        executorService.shutdown();
    }
}
