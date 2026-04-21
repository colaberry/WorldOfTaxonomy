import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Providers } from "@/components/Providers";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://worldoftaxonomy.com"),
  title: {
    default: "WorldOfTaxonomy - Global Classification Knowledge Graph",
    template: "%s | WorldOfTaxonomy",
  },
  description:
    "Explore 1,000+ global classification systems with 1.2M+ codes. Search NAICS, ISIC, HS, ICD, SOC codes and discover cross-system mappings.",
  keywords: [
    "NAICS codes",
    "ISIC codes",
    "HS codes",
    "industry classification",
    "taxonomy",
    "crosswalk",
    "ICD-10",
    "SOC codes",
    "NACE codes",
    "classification system",
  ],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://worldoftaxonomy.com",
    siteName: "WorldOfTaxonomy",
    title: "WorldOfTaxonomy - Global Classification Knowledge Graph",
    description:
      "1,000+ systems, 1.2M+ codes, 321K+ crosswalks. Search, browse, and translate classification codes across NAICS, ISIC, HS, ICD, and more.",
  },
  twitter: {
    card: "summary_large_image",
    site: "@ramdhanyk",
    creator: "@ramdhanyk",
    title: "WorldOfTaxonomy - Global Classification Knowledge Graph",
    description:
      "1,000+ systems, 1.2M+ codes, 321K+ crosswalks. Search, browse, and translate classification codes across NAICS, ISIC, HS, ICD, and more.",
  },
  robots: {
    index: true,
    follow: true,
    "max-snippet": -1,
    "max-image-preview": "large",
  },
  alternates: {
    canonical: "https://worldoftaxonomy.com",
  },
};

const jsonLd = [
  {
    "@context": "https://schema.org",
    "@type": "DataCatalog",
    name: "WorldOfTaxonomy",
    description:
      "Unified global classification knowledge graph with 1,000+ systems, 1.2M+ codes, and 321K+ crosswalk edges.",
    url: "https://worldoftaxonomy.com",
    creator: {
      "@type": "Organization",
      name: "Colaberry",
      url: "https://colaberry.com",
    },
    license: "https://opensource.org/licenses/MIT",
    numberOfItems: 1000,
  },
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "WorldOfTaxonomy",
    url: "https://worldoftaxonomy.com",
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: "https://worldoftaxonomy.com/explore?q={search_term_string}",
      },
      "query-input": "required name=search_term_string",
    },
  },
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "WorldOfTaxonomy",
    url: "https://worldoftaxonomy.com",
    logo: "https://worldoftaxonomy.com/opengraph-image",
    sameAs: [
      "https://github.com/colaberry/WorldOfTaxonomy",
    ],
    parentOrganization: {
      "@type": "Organization",
      name: "Colaberry AI",
      url: "https://colaberry.ai",
    },
  },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <link
          rel="alternate"
          type="application/rss+xml"
          title="WorldOfTaxonomy Blog"
          href="/feed.xml"
        />
      </head>
      <body className="min-h-full flex flex-col">
        <Providers>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
