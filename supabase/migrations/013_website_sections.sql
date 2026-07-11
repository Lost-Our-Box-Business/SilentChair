-- Website dynamic content sections
-- Stores AI-generated and user-editable content blocks (testimonials, team, portfolio, blog posts)
-- that are served publicly via the /public/website/{id}/sections API

CREATE TABLE website_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
  type TEXT NOT NULL,            -- 'testimonial' | 'team_member' | 'portfolio_item' | 'blog_post'
  title TEXT,
  subtitle TEXT,
  body TEXT,
  image_url TEXT,
  metadata JSONB DEFAULT '{}',  -- type-specific: {rating, linkedin_url, tags, result_metric, slug, excerpt, etc.}
  display_order INTEGER DEFAULT 0,
  is_published BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON website_sections(website_id, type, display_order);
