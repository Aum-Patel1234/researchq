package researchpaperapis

import (
	"encoding/xml"
)

// Feed is the top-level XML response
type Feed struct {
	XMLName xml.Name     `xml:"feed"`
	Entries []ArxivEntry `xml:"entry"`
}

type ArxivEntry struct {
	XMLName   xml.Name      `xml:"entry"`
	ID        string        `xml:"id"`
	Title     string        `xml:"title"`
	Updated   string        `xml:"updated"`
	Summary   string        `xml:"summary"`
	Published string        `xml:"published"`
	Category  Category      `xml:"category"`
	Author    []ArxivAuthor `xml:"author"`
	Link      []Link        `xml:"link"`

	ArxivComment         string          `xml:"comment,omitempty"`
	ArxivPrimaryCategory PrimaryCategory `xml:"primary_category,omitempty"`
	ArxivJournalRef      string          `xml:"journal_ref,omitempty"`
	ArxivDOI             string          `xml:"doi,omitempty"`
}

type Link struct {
	Href  string `xml:"href,attr"`
	Rel   string `xml:"rel,attr"`
	Type  string `xml:"type,attr,omitempty"`
	Title string `xml:"title,attr,omitempty"`
}

type Category struct {
	Term   string `xml:"term,attr"`
	Scheme string `xml:"scheme,attr,omitempty"`
}

type PrimaryCategory struct {
	Term string `xml:"term,attr"`
}

type ArxivAuthor struct {
	Name string `xml:"name"`
}

// Semantic Scholar API

type SemanticSearchResponse struct {
	Total int             `json:"total"`
	Data  []SemanticPaper `json:"data"`
}

type SemanticPaper struct {
	PaperID          string           `json:"paperId"`
	Title            string           `json:"title"`
	Abstract         string           `json:"abstract"`
	Year             int              `json:"year"`
	Authors          []SemanticAuthor `json:"authors"`
	URL              string           `json:"url"`
	OpenAccessPdf    *OpenAccessPDF   `json:"openAccessPdf"`
	Venue            string           `json:"venue"`
	PublicationTypes []string         `json:"publicationTypes"`
	CitationCount    int              `json:"citationCount"`
	ReferenceCount   int              `json:"referenceCount"`
	FieldsOfStudy    []string         `json:"fieldsOfStudy"`
}

type SemanticAuthor struct {
	AuthorID   string `json:"authorId"`
	URL        string `json:"url"`
	PaperCount int    `json:"paperCount"`
}

type OpenAccessPDF struct {
	URL        *string `json:"url"`
	Status     *string `json:"status"`
	License    *string `json:"license"`
	Disclaimer *string `json:"disclaimer"`
}

// Springer Nature API
type SpringerResponse struct {
	APIMessage string       `json:"apiMessage"`
	Query      string       `json:"query"`
	Result     []ResultMeta `json:"result"`
	Records    []Record     `json:"records"`
}

type ResultMeta struct {
	Total            string `json:"total"`
	Start            string `json:"start"`
	PageLength       string `json:"pageLength"`
	RecordsDisplayed string `json:"recordsDisplayed"`
}

type Record struct {
	ContentType     string      `json:"contentType"`
	Identifier      string      `json:"identifier"`
	Language        string      `json:"language"`
	URL             []RecordURL `json:"url"`
	Title           string      `json:"title"`
	Creators        []Creator   `json:"creators"`
	PublicationName string      `json:"publicationName"`
	OpenAccess      string      `json:"openaccess"`
	DOI             string      `json:"doi"`
	Publisher       string      `json:"publisher"`
	PublisherName   string      `json:"publisherName"`
	PublicationDate string      `json:"publicationDate"`
	PublicationType string      `json:"publicationType"`
	ISSN            string      `json:"issn"`
	EISSN           string      `json:"eIssn"`
	Volume          string      `json:"volume"`
	Number          string      `json:"number"`
	ArticleNumber   string      `json:"article-number"`
	JournalID       string      `json:"journalId"`
	// PrintDate         string       `json:"printDate"`
	// OnlineDate        string       `json:"onlineDate"`
	// CoverDate         string       `json:"coverDate"`
	// Copyright         string       `json:"copyright"`
	Abstract string `json:"abstract"`
	// ConferenceInfo []string     `json:"conferenceInfo"`
	// Keyword        []string     `json:"keyword"`
	// Subjects       []string     `json:"subjects"`
	// Disciplines    []Discipline `json:"disciplines"`
}

type RecordURL struct {
	Format   string `json:"format"`
	Platform string `json:"platform"`
	Value    string `json:"value"`
}

type Creator struct {
	Creator string `json:"creator"`
}

// type Discipline struct {
// 	ID   string `json:"id"`
// 	Term string `json:"term"`
// }
