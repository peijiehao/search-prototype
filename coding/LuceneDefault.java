import java.io.*;
import java.util.*;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.*;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.ScoreDoc;
import org.apache.lucene.search.TopScoreDocCollector;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.Version;

/**
 * To create Apache Lucene index in a folder and add files into this index based
 * on the input of the user.
 */
public class LuceneDefault {

    // use StandardAnalyzer
    private static Analyzer analyzer = new StandardAnalyzer(Version.LUCENE_47);

    private IndexWriter writer;
    private ArrayList<File> queue = new ArrayList<File>();

    public static void main(String[] args) throws IOException {
        System.out
                .println("Enter the FULL path where the index will be created: (e.g. /Usr/index or c:\\temp\\index)");

        String indexLocation = null;
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String s = br.readLine();

        LuceneDefault indexer = null;
        try {
            indexLocation = s;
            indexer = new LuceneDefault(s);
        } catch (Exception ex) {
            System.out.println("Cannot create index..." + ex.getMessage());
            System.exit(-1);
        }

        // ===================================================
        // read input from user until he enters q for quit
        // ===================================================
        while (!s.equalsIgnoreCase("q")) {
            try {
                System.out
                        .println("Enter the FULL path to add into the index (q=quit): (e.g. /home/mydir/docs or c:\\Users\\mydir\\docs)");
                System.out
                        .println("[Acceptable file types: .xml, .html, .html, .txt]");
                s = br.readLine();
                if (s.equalsIgnoreCase("q")) {
                    break;
                }

                // try to add file into the index
                indexer.indexFileOrDirectory(s);
            } catch (Exception e) {
                System.out.println("Error indexing " + s + " : "
                        + e.getMessage());
            }
        }

        // ===================================================
        // after adding, we always have to call the
        // closeIndex, otherwise the index is not created
        // ===================================================
        indexer.closeIndex();

        // =========================================================
        // Now search
        // =========================================================
        s = "";
        // create a directory
        new File("task1/").mkdir();
        try {

            LinkedHashMap<Integer, String> queryMap = indexer.parseQuery("/Users/wandong/Desktop/prj/test-collection/cacm.query.txt");

            int cnt = 1;
            File file = new File("task1/results.txt");
            FileWriter fileWriter = new FileWriter(file);
            BufferedWriter output = new BufferedWriter(fileWriter);
            for (int queryId : queryMap.keySet()) {
                Map<String, Float> scores = new LinkedHashMap<>();
                IndexReader reader = DirectoryReader.open(FSDirectory.open(new File(
                        indexLocation)));
                IndexSearcher searcher = new IndexSearcher(reader);
                TopScoreDocCollector collector = TopScoreDocCollector.create(4000, true);
                System.out.println(queryId);
                s = queryMap.get(queryId);
                System.out.println(s);
                Query q = new QueryParser(Version.LUCENE_47, "contents",
                        analyzer).parse(QueryParser.escape(s));
                searcher.search(q, collector);
                ScoreDoc[] hits = collector.topDocs().scoreDocs;

                // 4. display results
                System.out.println("Found " + hits.length + " hits.");
                int limitLength = Math.min(100, hits.length);
                for (int i = 0; i < limitLength; ++i) {
                    int docId = hits[i].doc;
                    Document d = searcher.doc(docId);

                    // get docid
                    String fileName = d.get("filename").toString();
                    String docid = fileName.split(".html")[0];
                    scores.put(docid, hits[i].score);
                    System.out.println((i + 1) + " " + docid
                            + " score=" + hits[i].score);
                }

                // create new file to store the results

                output.write("results for query " + cnt);
                output.newLine();
                for (String docid : scores.keySet()) {
                    output.write(cnt + " Q0 " + docid + " rank: " + scores.get(docid));
                    output.newLine();
                }
                cnt++;
            }
            output.close();

        } catch (Exception e) {
            System.out.println("Error searching " + s + " : "
                    + e.getMessage());
        }


    }

    /**
     * Constructor
     *
     * @param indexDir
     *            the name of the folder in which the index should be created
     * @throws java.io.IOException
     *             when exception creating index.
     */
    LuceneDefault(String indexDir) throws IOException {

        FSDirectory dir = FSDirectory.open(new File(indexDir));

        IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_47,
                analyzer);

        writer = new IndexWriter(dir, config);
    }

    /**
     * Indexes a file or directory
     *
     * @param fileName
     *            the name of a text file or a folder we wish to add to the
     *            index
     * @throws java.io.IOException
     *             when exception
     */
    public void indexFileOrDirectory(String fileName) throws IOException {
        // ===================================================
        // gets the list of files in a folder (if user has submitted
        // the name of a folder) or gets a single file name (is user
        // has submitted only the file name)
        // ===================================================
        addFiles(new File(fileName));

        int originalNumDocs = writer.numDocs();
        for (File f : queue) {
            FileReader fr = null;
            try {
                Document doc = new Document();

                // ===================================================
                // add contents of file
                // ===================================================
                fr = new FileReader(f);
                doc.add(new TextField("contents", fr));
                doc.add(new StringField("path", f.getPath(), Field.Store.YES));
                doc.add(new StringField("filename", f.getName(),
                        Field.Store.YES));

                writer.addDocument(doc);
                System.out.println("Added: " + f);
            } catch (Exception e) {
                System.out.println("Could not add: " + f);
            } finally {
                fr.close();
            }
        }

        int newNumDocs = writer.numDocs();
        System.out.println("");
        System.out.println("************************");
        System.out
                .println((newNumDocs - originalNumDocs) + " documents added.");
        System.out.println("************************");

        queue.clear();
    }

    private void addFiles(File file) {

        if (!file.exists()) {
            System.out.println(file + " does not exist.");
        }
        if (file.isDirectory()) {
            for (File f : file.listFiles()) {
                addFiles(f);
            }
        } else {
            String filename = file.getName().toLowerCase();
            // ===================================================
            // Only index text files
            // ===================================================
            if (filename.endsWith(".htm") || filename.endsWith(".html")
                    || filename.endsWith(".xml") || filename.endsWith(".txt")) {
                queue.add(file);
            } else {
                System.out.println("Skipped " + filename);
            }
        }
    }

    /**
     * Close the index.
     *
     * @throws java.io.IOException
     *             when exception closing
     */
    public void closeIndex() throws IOException {
        writer.close();
    }

    private LinkedHashMap parseQuery(String pathName) throws IOException{
        File fileName = new File(pathName);
        InputStreamReader reader = new InputStreamReader(
                new FileInputStream(fileName));
        BufferedReader br = new BufferedReader(reader);
        String line = "";
        StringBuilder content = new StringBuilder();
        LinkedHashMap<Integer, String> queryMap = new LinkedHashMap<>();
        while (line != null) {
            line = br.readLine();
            content.append(line);
        }

        while (content.indexOf("<DOCNO>") != -1) {
            int index1 = content.indexOf("<DOCNO>");
            int index2 = content.indexOf("</DOCNO>");
            int index3 = content.indexOf("</DOC>");
            int queryId = Integer.parseInt(content.substring(index1 + 8, index2 - 1));
            String queryStr = content.substring(index2 + 8, index3 - 1);
            queryStr = queryStr.trim();

            queryMap.put(queryId, queryStr);
            content.delete(0, index3 + 6);
        }
        return queryMap;
    }
}