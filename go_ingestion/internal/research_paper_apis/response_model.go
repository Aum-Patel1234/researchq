package researchpaperapis

import "encoding/xml"

// Feed is the top-level XML response
type Feed struct {
	XMLName xml.Name     `xml:"feed"`
	Entries []ArxivEntry `xml:"entry"`
}

type ArxivEntry struct {
	XMLName   xml.Name `xml:"entry"`
	ID        string   `xml:"id"`
	Title     string   `xml:"title"`
	Updated   string   `xml:"updated"`
	Summary   string   `xml:"summary"`
	Published string   `xml:"published"`
	Category  Category `xml:"category"`
	Author    []Author `xml:"author"`
	Link      []Link   `xml:"link"`

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

type Author struct {
	Name string `xml:"name"`
}
