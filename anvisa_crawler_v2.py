"""
ANVISA Crawler v2.0.1 - FIXED TABLE ROW CLICKING
==================================================

CRITICAL FIX:
✅ Now clicks on ROWS, not individual cells
✅ Groups table cells by parent row
✅ Clicks only the first cell of each row
✅ Properly handles both search flows

IMPROVEMENTS:
✅ Collects ALL presentations with full details
✅ Collects ALL document links (Bulário, Parecer, Rotulagem)
✅ Better click strategy with retry mechanisms
✅ 50 results per page pagination
✅ More robust Angular page handling
✅ Comprehensive error handling

Uses same stealth techniques as v1.0
"""

import asyncio
import logging
import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger("anvisa")

# Same proxies as Google Patents crawler
PROXIES = [
    "http://brd-customer-hl_8ea11d75-zone-residential_proxy1:w7qs41l7ijfc@brd.superproxy.io:33335",
    "http://brd-customer-hl_8ea11d75-zone-datacenter_proxy1:93u1xg5fef4p@brd.superproxy.io:33335",
    "http://5SHQXNTHNKDHUHFD:wifi;us;;;@proxy.scrapingbee.com:8886",
    "http://XNK2KLGACMN0FKRY:wifi;us;;;@proxy.scrapingbee.com:8886",
]


class AnvisaCrawlerV2:
    """Anvisa Brazilian Regulatory Agency Crawler - Fixed Version"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.proxy_index = 0
        
    def _get_next_proxy(self) -> str:
        """Rotate proxies"""
        proxy = PROXIES[self.proxy_index % len(PROXIES)]
        self.proxy_index += 1
        return proxy
    
    async def _translate_to_portuguese(
        self,
        molecule: str,
        brand: str,
        groq_api_key: str
    ) -> tuple[str, str]:
        """Translate molecule and brand to Portuguese using Groq"""
        if not groq_api_key:
            logger.warning("   ⚠️ No Groq API key - using English terms")
            return molecule, brand
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                prompt = f"""Translate these pharmaceutical terms to Brazilian Portuguese:
                
Molecule: {molecule}
Brand: {brand if brand else 'N/A'}

Reply ONLY with JSON format:
{{
    "molecule_pt": "...",
    "brand_pt": "..."
}}

Rules:
- Use Brazilian Portuguese (pt-BR)
- Keep chemical names accurate
- If brand is N/A, return empty string
- No explanations, just JSON"""

                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 200
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    
                    import json
                    translations = json.loads(content)
                    
                    molecule_pt = translations.get('molecule_pt', molecule).strip()
                    brand_pt = translations.get('brand_pt', brand).strip() if brand else ""
                    
                    return molecule_pt, brand_pt
                else:
                    logger.warning(f"   ⚠️ Groq API error: {response.status_code}")
                    return molecule, brand
                    
        except Exception as e:
            logger.warning(f"   ⚠️ Translation error: {str(e)}")
            return molecule, brand
    
    async def search_anvisa(
        self,
        molecule: str,
        brand: str = None,
        groq_api_key: str = None,
        use_proxy: bool = False
    ) -> Dict:
        """
        Search Anvisa for drug registrations - FULL DATA EXTRACTION
        
        Args:
            molecule: Molecule name (English)
            brand: Brand name (optional)
            groq_api_key: Groq API key for translation
            use_proxy: Use proxy rotation
        
        Returns:
            Dict with found products and summary
        """
        logger.info("=" * 100)
        logger.info(f"🏥 ANVISA SEARCH V2.0.1: {molecule}" + (f" ({brand})" if brand else ""))
        logger.info("=" * 100)
        
        # Translate to Portuguese
        molecule_pt, brand_pt = await self._translate_to_portuguese(
            molecule, brand, groq_api_key
        )
        
        logger.info(f"   ✅ Translations:")
        logger.info(f"      Molecule: {molecule} → {molecule_pt}")
        if brand:
            logger.info(f"      Brand: {brand} → {brand_pt}")
        
        all_products = []
        
        try:
            async with async_playwright() as p:
                # Launch browser with stealth
                launch_args = {
                    'headless': True,
                    'args': [
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                }
                
                if use_proxy:
                    proxy_url = self._get_next_proxy()
                    logger.info(f"   🔄 Using proxy: {proxy_url[:50]}...")
                    launch_args['proxy'] = {'server': proxy_url}
                
                self.browser = await p.chromium.launch(**launch_args)
                
                self.context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='pt-BR'
                )
                
                self.page = await self.context.new_page()
                
                # Strategy 1: Try brand name search (more specific)
                if brand_pt:
                    logger.info(f"   🔍 Strategy 1: Searching by brand name '{brand_pt}'...")
                    products = await self._search_by_brand_name(brand_pt)
                    if products:
                        logger.info(f"      ✅ Found {len(products)} products via brand name")
                        all_products.extend(products)
                
                # Strategy 2: Search by active ingredient (more comprehensive)
                if not all_products:
                    logger.info(f"   🔍 Strategy 2: Searching by active ingredient '{molecule_pt}'...")
                    products = await self._search_by_active_ingredient(molecule_pt)
                    if products:
                        logger.info(f"      ✅ Found {len(products)} products via active ingredient")
                        all_products.extend(products)
                
                await self.browser.close()
                
        except Exception as e:
            logger.error(f"   ❌ Search error: {str(e)}")
            if self.browser:
                await self.browser.close()
        
        # Build response
        logger.info(f"✅ Search completed: {len(all_products)} products found")
        
        return {
            'found': len(all_products) > 0,
            'products': all_products,
            'summary': self._build_summary(all_products),
            'search_terms': {
                'molecule': molecule,
                'molecule_pt': molecule_pt,
                'brand': brand or "",
                'brand_pt': brand_pt or ""
            }
        }
    
    async def _search_by_brand_name(self, brand_name: str) -> List[Dict]:
        """Search by brand name (Nome do Produto) - FLOW 1"""
        products = []
        
        try:
            # Build URL
            url = f"https://consultas.anvisa.gov.br/#/medicamentos/q/?nomeProduto={brand_name}"
            logger.info(f"      → URL: {url}")
            
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)  # Wait for Angular to render
            
            # Try to increase pagination to 50 results
            await self._set_pagination_50()
            
            # Parse results
            products = await self._parse_results_table_fixed()
            
        except Exception as e:
            logger.warning(f"      ⚠️ Brand name search error: {str(e)}")
        
        return products
    
    async def _search_by_active_ingredient(self, molecule: str) -> List[Dict]:
        """Search by active ingredient (Princípio Ativo) - FLOW 2 - ADVANCED SEARCH"""
        products = []
        
        try:
            # 1. Go to main page
            logger.info("      → Step 1: Going to main page...")
            await self.page.goto(
                "https://consultas.anvisa.gov.br/#/medicamentos/",
                wait_until='networkidle',
                timeout=30000
            )
            await asyncio.sleep(2)
            
            # 2. Click "Busca Avançada"
            logger.info("      → Step 2: Clicking 'Busca Avançada'...")
            try:
                await self.page.wait_for_selector('input[value="Busca Avançada"]', timeout=5000)
                await self.page.click('input[value="Busca Avançada"]')
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"         ⚠️ Could not click Busca Avançada: {e}")
                return products
            
            # 3. Click search icon next to "Princípio Ativo"
            logger.info("      → Step 3: Opening molecule search dialog...")
            try:
                # Wait for the search icon to appear
                await self.page.wait_for_selector('i.glyphicon-search', timeout=5000)
                await self.page.click('i.glyphicon-search', timeout=5000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"         ⚠️ Could not click search icon: {e}")
                return products
            
            # 4. Type molecule name in modal
            logger.info(f"      → Step 4: Typing '{molecule}' in search...")
            try:
                await self.page.wait_for_selector('input[ng-model="filter.nome"]', timeout=5000)
                await self.page.fill('input[ng-model="filter.nome"]', molecule)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"         ⚠️ Could not type molecule name: {e}")
                return products
            
            # 5. Click "Pesquisar" button in modal
            logger.info("      → Step 5: Clicking 'Pesquisar' in modal...")
            try:
                await self.page.click('input[value="Pesquisar"][type="submit"]', timeout=5000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"         ⚠️ Could not click Pesquisar: {e}")
                return products
            
            # 6. Click checkbox/select icon for first result
            logger.info("      → Step 6: Selecting molecule from results...")
            try:
                await self.page.wait_for_selector('a:has(i.glyphicon-check)', timeout=5000)
                await self.page.click('a:has(i.glyphicon-check)', timeout=5000)
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"         ⚠️ Could not select molecule: {e}")
                return products
            
            # 7. Click final "Consultar" button
            logger.info("      → Step 7: Clicking final 'Consultar'...")
            try:
                await self.page.click('input.btn-primary[value="Consultar"]', timeout=5000)
                await asyncio.sleep(3)
            except Exception as e:
                logger.warning(f"         ⚠️ Could not click Consultar: {e}")
                return products
            
            # 8. Try to increase pagination to 50
            await self._set_pagination_50()
            
            # 9. Parse results
            products = await self._parse_results_table_fixed()
            
        except Exception as e:
            logger.warning(f"      ⚠️ Active ingredient search error: {str(e)}")
        
        return products
    
    async def _set_pagination_50(self):
        """Try to set pagination to 50 results per page"""
        try:
            # Check if pagination buttons exist
            html = await self.page.content()
            if '50' in html and 'btn-default' in html:
                logger.info("      → Setting pagination to 50 results...")
                # Try clicking 50 button
                await self.page.click('button:has-text("50")', timeout=5000)
                await asyncio.sleep(2)
                logger.info("      → Pagination set to 50")
            else:
                logger.info("      → Pagination not needed (< 10 results)")
        except Exception as e:
            logger.debug(f"      → Pagination button not found or not needed: {str(e)}")
    
    async def _parse_results_table_fixed(self) -> List[Dict]:
        """
        🔧 FIXED: Parse results table by clicking ROWS, not individual cells
        
        NEW Strategy:
        1. Get all table rows (tr)
        2. For each row, find cells with ng-click
        3. Group cells by parent row
        4. Click only the FIRST cell of each row
        5. Parse product details
        6. Go back
        
        This fixes the issue where we were clicking individual cells
        (NUBEQA, REGISTRADO, DAROLUTAMIDA, etc.) instead of clicking
        once per product row.
        """
        products = []
        
        try:
            # Wait for table to be ready
            await self.page.wait_for_selector('table', timeout=10000)
            await asyncio.sleep(2)
            
            # Get page HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 🔧 FIX: Find table rows (tr), not individual cells
            # Look for tbody (table body) which contains the data rows
            tbody = soup.find('tbody')
            
            if not tbody:
                logger.warning("      ⚠️ No tbody found in table")
                return products
            
            # Get all rows in the table body
            table_rows = tbody.find_all('tr', recursive=False)
            
            logger.info(f"      → Found {len(table_rows)} result rows")
            
            if not table_rows:
                return products
            
            # Process each row (limit to avoid excessive runtime)
            max_products = min(len(table_rows), 50)  # Process up to 50 products
            
            for i in range(max_products):
                try:
                    # Re-get the page content (important after navigation)
                    await asyncio.sleep(1)
                    html = await self.page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    tbody = soup.find('tbody')
                    if not tbody:
                        break
                    
                    table_rows = tbody.find_all('tr', recursive=False)
                    
                    if i >= len(table_rows):
                        break
                    
                    # Get current row
                    row = table_rows[i]
                    
                    # Get all cells in this row
                    cells = row.find_all('td')
                    
                    if not cells:
                        logger.warning(f"      ⚠️ Row {i+1} has no cells")
                        continue
                    
                    # Get first cell text for logging
                    first_cell_text = cells[0].get_text(strip=True)
                    
                    logger.info(f"      → [{i+1}/{max_products}] Clicking: {first_cell_text}...")
                    
                    # 🔧 KEY FIX: Use JavaScript to click the FIRST cell of THIS row
                    # This ensures we click once per product, not once per cell
                    js_click = f"""
                    var tbody = document.querySelector('tbody');
                    if (!tbody) return false;
                    
                    var rows = tbody.querySelectorAll('tr');
                    if (!rows[{i}]) return false;
                    
                    var cells = rows[{i}].querySelectorAll('td');
                    if (!cells[0]) return false;
                    
                    // Click the first cell of this row
                    cells[0].click();
                    return true;
                    """
                    
                    clicked = await self.page.evaluate(js_click)
                    
                    if not clicked:
                        logger.warning(f"         ⚠️ Could not click row {i+1}")
                        continue
                    
                    # Wait for detail page to load
                    await asyncio.sleep(3)
                    
                    # Wait for detail page elements
                    try:
                        await self.page.wait_for_selector('table', timeout=10000)
                    except PlaywrightTimeout:
                        logger.warning(f"         ⚠️ Timeout waiting for detail page on row {i+1}")
                        await self.page.go_back(timeout=5000)
                        await asyncio.sleep(2)
                        continue
                    
                    # Parse product details (FULL EXTRACTION)
                    product = await self._parse_product_details_v2()
                    
                    if product:
                        products.append(product)
                        logger.info(f"         ✅ Parsed: {product.get('product_name', 'Unknown')}")
                        logger.info(f"            → Presentations: {len(product.get('presentations', []))}")
                        logger.info(f"            → Links: Bulário={bool(product.get('links', {}).get('bulario'))}, "
                                  f"Parecer={bool(product.get('links', {}).get('parecer_publico'))}, "
                                  f"Rotulagem={len(product.get('links', {}).get('rotulagem', []))}")
                    
                    # Go back to results
                    await self.page.go_back()
                    await asyncio.sleep(2)
                    await self.page.wait_for_selector('table', timeout=10000)
                    
                except PlaywrightTimeout:
                    logger.warning(f"         ⚠️ Timeout on product {i+1}")
                    # Try to recover
                    try:
                        await self.page.go_back(timeout=5000)
                        await asyncio.sleep(2)
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"         ⚠️ Error parsing product {i+1}: {str(e)}")
                    # Try to go back if stuck
                    try:
                        await self.page.go_back(timeout=5000)
                        await asyncio.sleep(2)
                    except:
                        pass
            
        except Exception as e:
            logger.warning(f"      ⚠️ Table parsing error: {str(e)}")
        
        return products
    
    async def _parse_product_details_v2(self) -> Optional[Dict]:
        """
        Parse product detail page - FULL DATA EXTRACTION
        
        Extracts:
        - All basic fields
        - ALL presentations with complete details
        - ALL document links (Bulário, Parecer, Rotulagem)
        """
        try:
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            product = {}
            
            # Helper function to find value by label
            def find_value_by_label(label_text: str) -> str:
                label = soup.find(string=lambda x: x and label_text in x)
                if label:
                    parent = label.find_parent()
                    if parent:
                        next_td = parent.find_next_sibling()
                        if next_td:
                            value = next_td.get_text(strip=True)
                            # Ignore values that look like labels
                            label_keywords = ['Número', 'Data', 'Empresa', 'Categoria', 'Medicamento', 
                                            'Classe', 'Tipo', 'Complemento', 'Princípio', 'Vencimento',
                                            'Situação', 'Regularização']
                            is_header = any(kw in value for kw in label_keywords) and len(value) > 10
                            if not is_header:
                                return value
                return ""
            
            # Extract all basic fields
            product['product_name'] = find_value_by_label('Nome do Produto')
            product['complement'] = find_value_by_label('Complemento da Marca')
            product['process_number'] = find_value_by_label('Número do Processo')
            product['registration_number'] = find_value_by_label('Número da Regularização')
            product['registration_date'] = find_value_by_label('Data da Regularização')
            product['expiry_date'] = find_value_by_label('Vencimento da Regularização')
            product['company'] = find_value_by_label('Empresa Detentora da Regularização')
            product['cnpj'] = find_value_by_label('CNPJ')
            product['afe'] = find_value_by_label('AFE')
            product['active_ingredient'] = find_value_by_label('Princípio Ativo')
            product['regulatory_category'] = find_value_by_label('Categoria Regulatória')
            product['reference_drug'] = find_value_by_label('Medicamento de referência')
            product['therapeutic_class'] = find_value_by_label('Classe Terapêutica')
            product['atc_code'] = find_value_by_label('ATC')
            product['priority_type'] = find_value_by_label('Tipo de Priorização')
            
            # Extract ALL document links
            product['links'] = self._extract_document_links(soup)
            
            # Extract ALL presentations
            product['presentations'] = self._extract_presentations(soup)
            
            # Only return if we got minimum data
            if product.get('product_name') and product.get('active_ingredient'):
                return product
            else:
                return None
                
        except Exception as e:
            logger.warning(f"         ⚠️ Detail parsing error: {str(e)}")
            return None
    
    def _extract_document_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract all document links from product page
        
        Returns dict with keys:
        - bulario: Link to Bulário Eletrônico
        - parecer_publico: Link to Parecer Público  
        - rotulagem: List of rotulagem PDF links
        """
        links = {
            'bulario': '',
            'parecer_publico': '',
            'rotulagem': []
        }
        
        try:
            # Find "Bulário Eletrônico" link
            bulario_label = soup.find(string=lambda x: x and 'Bulário Eletrônico' in x)
            if bulario_label:
                parent = bulario_label.find_parent()
                if parent:
                    next_td = parent.find_next_sibling()
                    if next_td:
                        link = next_td.find('a')
                        if link and link.get('href'):
                            links['bulario'] = link.get('href')
            
            # Find "Parecer Público" link
            parecer_label = soup.find(string=lambda x: x and 'Parecer Público' in x)
            if parecer_label:
                parent = parecer_label.find_parent()
                if parent:
                    next_td = parent.find_next_sibling()
                    if next_td:
                        link = next_td.find('a')
                        if link and link.get('href'):
                            links['parecer_publico'] = link.get('href')
            
            # Find "Rotulagem" links (can be multiple PDFs)
            rotulagem_label = soup.find(string=lambda x: x and 'Rotulagem' in x)
            if rotulagem_label:
                parent = rotulagem_label.find_parent()
                if parent:
                    next_td = parent.find_next_sibling()
                    if next_td:
                        # Find all links in this cell
                        all_links = next_td.find_all('a')
                        for link in all_links:
                            if link.get_text(strip=True):  # Has text
                                links['rotulagem'].append({
                                    'filename': link.get_text(strip=True),
                                    'url': link.get('href', '')
                                })
            
        except Exception as e:
            logger.debug(f"         → Error extracting links: {str(e)}")
        
        return links
    
    def _extract_presentations(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract ALL presentations from the presentations table
        
        Table structure:
        Nº | Apresentação | Registro | Forma Farmacêutica | Data de Publicação | Validade
        
        Returns list of dicts with all presentation details
        """
        presentations = []
        
        try:
            # Find the presentations table
            # Look for table headers: Nº, Apresentação, Registro, etc.
            tables = soup.find_all('table')
            
            for table in tables:
                # Check if this is the presentations table
                headers = table.find_all('th')
                header_texts = [h.get_text(strip=True) for h in headers]
                
                # Check for key headers
                if 'Apresentação' in str(header_texts) or 'Registro' in str(header_texts):
                    # This is the presentations table
                    rows = table.find_all('tr')
                    
                    for row in rows[1:]:  # Skip header row
                        cols = row.find_all('td')
                        
                        if len(cols) >= 5:  # Minimum columns expected
                            presentation = {
                                'number': cols[0].get_text(strip=True) if len(cols) > 0 else '',
                                'description': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                                'registration': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                                'pharmaceutical_form': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                                'publication_date': cols[4].get_text(strip=True) if len(cols) > 4 else '',
                                'validity': cols[5].get_text(strip=True) if len(cols) > 5 else ''
                            }
                            
                            # Only add if has meaningful data
                            if presentation['description']:
                                presentations.append(presentation)
                    
                    break  # Found the table, no need to continue
            
        except Exception as e:
            logger.debug(f"         → Error extracting presentations: {str(e)}")
        
        return presentations
    
    def _build_summary(self, products: List[Dict]) -> Dict:
        """Build summary statistics"""
        if not products:
            return {
                'total_products': 0,
                'total_presentations': 0,
                'first_approval': None,
                'reference_drugs': 0,
                'generic_drugs': 0,
                'companies': [],
                'documents_available': {
                    'bulario': 0,
                    'parecer_publico': 0,
                    'rotulagem': 0
                }
            }
        
        # Analyze products
        reference_count = 0
        generic_count = 0
        companies = set()
        dates = []
        total_presentations = 0
        bulario_count = 0
        parecer_count = 0
        rotulagem_count = 0
        
        for p in products:
            # Count presentations
            total_presentations += len(p.get('presentations', []))
            
            # Count documents
            links = p.get('links', {})
            if links.get('bulario'):
                bulario_count += 1
            if links.get('parecer_publico'):
                parecer_count += 1
            if links.get('rotulagem'):
                rotulagem_count += 1
            
            # Reference/Generic classification
            if p.get('reference_drug'):
                if 'REFERÊNCIA' in p['reference_drug'].upper():
                    reference_count += 1
                elif 'GENÉRICO' in p['reference_drug'].upper():
                    generic_count += 1
            
            if p.get('company'):
                companies.add(p['company'])
            
            if p.get('registration_date'):
                dates.append(p['registration_date'])
        
        # Find earliest date
        first_date = None
        if dates:
            try:
                parsed_dates = []
                for d in dates:
                    parts = d.split('/')
                    if len(parts) == 3:
                        parsed_dates.append(f"{parts[2]}-{parts[1]}-{parts[0]}")
                if parsed_dates:
                    first_date = min(parsed_dates)
            except:
                pass
        
        return {
            'total_products': len(products),
            'total_presentations': total_presentations,
            'first_approval': first_date,
            'reference_drugs': reference_count,
            'generic_drugs': generic_count,
            'companies': sorted(list(companies)),
            'documents_available': {
                'bulario': bulario_count,
                'parecer_publico': parecer_count,
                'rotulagem': rotulagem_count
            }
        }


# Singleton instance
anvisa_crawler_v2 = AnvisaCrawlerV2()
