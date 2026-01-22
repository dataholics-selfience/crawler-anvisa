"""
ANVISA Crawler v1.1 - FIXED VERSION
Regulatory Intelligence for Brazilian Market

FIXES:
✅ Better waits for AngularJS elements
✅ Explicit wait_for_selector with 'visible' state
✅ Multiple click strategies (retry mechanism)
✅ Better element detection for "Busca Avançada"
✅ Improved active ingredient search flow

Uses EXACT same technique as INPI crawler:
✅ Playwright 1.48.0
✅ Stealth (disable automation flags + custom user agent)
✅ Proxy rotation (Bright Data + ScrapingBee)
✅ Groq AI for adaptive parsing
✅ Retry mechanisms

Flow:
1. Try brand name search first (more specific)
2. Fallback to active ingredient search with improved waits
3. Click through results
4. Parse product details

Website: https://consultas.anvisa.gov.br/#/medicamentos/
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


class AnvisaCrawler:
    """Anvisa Brazilian Regulatory Agency Crawler - FIXED VERSION"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.proxy_index = 0
        
    def _get_next_proxy(self) -> str:
        """Rotate proxies (same as Google Patents)"""
        proxy = PROXIES[self.proxy_index % len(PROXIES)]
        self.proxy_index += 1
        return proxy
    
    async def _translate_to_portuguese(
        self,
        molecule: str,
        brand: str,
        groq_api_key: str
    ) -> tuple[str, str]:
        """
        Translate molecule and brand to Portuguese using Groq
        Same logic as INPI crawler
        """
        if not groq_api_key:
            logger.warning("   ⚠️ No Groq API key - using English terms")
            return molecule, brand
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build prompt
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
                    
                    # Parse JSON response
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
    
    async def _wait_for_angular(self):
        """Wait for AngularJS to finish loading"""
        try:
            # Wait for Angular to be ready
            await self.page.wait_for_function(
                """
                () => {
                    return typeof angular !== 'undefined' && 
                           angular.element(document).injector() &&
                           angular.element(document).injector().get('$http').pendingRequests.length === 0;
                }
                """,
                timeout=10000
            )
        except:
            # Fallback: just wait
            await asyncio.sleep(2)
    
    async def _click_with_retry(self, selector: str, description: str, max_retries: int = 3):
        """Click element with retry mechanism"""
        for attempt in range(max_retries):
            try:
                # Wait for element to be visible
                await self.page.wait_for_selector(selector, state='visible', timeout=15000)
                
                # Extra wait for any animations
                await asyncio.sleep(0.5)
                
                # Try to click
                await self.page.click(selector, timeout=10000)
                logger.info(f"      ✅ Successfully clicked: {description}")
                return True
                
            except Exception as e:
                logger.warning(f"      ⚠️ Attempt {attempt + 1}/{max_retries} failed for {description}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise
        
        return False
    
    async def search_anvisa(
        self,
        molecule: str,
        brand: str = None,
        groq_api_key: str = None,
        use_proxy: bool = False
    ) -> Dict:
        """
        Search Anvisa for drug registrations
        
        Args:
            molecule: Molecule name (English)
            brand: Brand name (optional)
            groq_api_key: Groq API key for translation
            use_proxy: Use proxy rotation (default: False for testing)
        
        Returns:
            Dict with found products and summary
        """
        logger.info("=" * 100)
        logger.info(f"🏥 ANVISA SEARCH: {molecule}" + (f" ({brand})" if brand else ""))
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
                # Launch browser with stealth (same as INPI)
                launch_args = {
                    'headless': True,
                    'args': [
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                }
                
                # Add proxy if requested
                if use_proxy:
                    proxy_url = self._get_next_proxy()
                    logger.info(f"   🔄 Using proxy: {proxy_url[:50]}...")
                    launch_args['proxy'] = {'server': proxy_url}
                
                self.browser = await p.chromium.launch(**launch_args)
                
                self.context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
            logger.error(f"   ❌ Anvisa search error: {str(e)}")
            if self.browser:
                await self.browser.close()
        
        # Build response
        return {
            'found': len(all_products) > 0,
            'products': all_products,
            'summary': self._build_summary(all_products),
            'search_terms': {
                'molecule': molecule,
                'molecule_pt': molecule_pt,
                'brand': brand,
                'brand_pt': brand_pt
            }
        }
    
    async def _search_by_brand_name(self, brand_name: str) -> List[Dict]:
        """
        Search by brand name (commercial name)
        URL: https://consultas.anvisa.gov.br/#/medicamentos/q/?nomeProduto=xxx
        """
        products = []
        
        try:
            # Navigate to search page with brand name
            url = f"https://consultas.anvisa.gov.br/#/medicamentos/q/?nomeProduto={brand_name}"
            logger.info(f"      → URL: {url}")
            
            await self.page.goto(url, wait_until='networkidle', timeout=30000)
            await self._wait_for_angular()
            
            # Try to set pagination to 50 (if available)
            try:
                button_50 = await self.page.wait_for_selector(
                    'button:has-text("50")',
                    timeout=3000
                )
                await button_50.click()
                await asyncio.sleep(1)
                logger.info("      → Pagination set to 50")
            except:
                logger.info("      → Pagination not needed (< 10 results)")
            
            # Get all result rows
            products = await self._parse_results_table()
            
        except Exception as e:
            logger.warning(f"      ⚠️ Brand name search error: {str(e)}")
        
        return products
    
    async def _search_by_active_ingredient(self, molecule: str) -> List[Dict]:
        """
        Search by active ingredient (princípio ativo)
        FIXED VERSION: Better waits and element detection
        """
        products = []
        
        try:
            # 1. Go to main page
            logger.info("      → Step 1: Opening main search page...")
            await self.page.goto(
                'https://consultas.anvisa.gov.br/#/medicamentos/',
                wait_until='networkidle',
                timeout=30000
            )
            await self._wait_for_angular()
            await asyncio.sleep(2)  # Extra wait for page stability
            
            # 2. Click "Busca Avançada" - FIXED WITH RETRY
            logger.info("      → Step 2: Clicking 'Busca Avançada'...")
            
            # Try multiple strategies to find and click the button
            clicked = False
            
            # Strategy A: By value attribute
            try:
                await self._click_with_retry(
                    'input[value="Busca Avançada"]',
                    "Busca Avançada (by value)",
                    max_retries=2
                )
                clicked = True
            except:
                pass
            
            # Strategy B: By ng-click attribute
            if not clicked:
                try:
                    await self._click_with_retry(
                        'input[ng-click="toggleBuscaAvancada()"]',
                        "Busca Avançada (by ng-click)",
                        max_retries=2
                    )
                    clicked = True
                except:
                    pass
            
            # Strategy C: By text content (button or input)
            if not clicked:
                try:
                    await self._click_with_retry(
                        'button:has-text("Busca Avançada"), input:has-text("Busca Avançada")',
                        "Busca Avançada (by text)",
                        max_retries=2
                    )
                    clicked = True
                except:
                    pass
            
            if not clicked:
                raise Exception("Could not click 'Busca Avançada' button")
            
            await asyncio.sleep(1)
            
            # 3. Click magnifying glass icon next to "Princípio Ativo" - FIXED
            logger.info("      → Step 3: Opening active ingredient search...")
            
            # Wait for the "Princípio Ativo" section to be visible
            await self.page.wait_for_selector('text=Princípio Ativo', state='visible', timeout=10000)
            
            # Find the search icon specifically in the "Princípio Ativo" section
            # Look for the parent label, then find the icon inside it
            try:
                # Try to click the icon that's specifically next to "Princípio Ativo"
                await self.page.evaluate("""
                    () => {
                        const labels = Array.from(document.querySelectorAll('label'));
                        const principioLabel = labels.find(l => l.textContent.includes('Princípio Ativo'));
                        if (principioLabel) {
                            const icon = principioLabel.closest('.form-group, div').querySelector('i.glyphicon-search');
                            if (icon) {
                                icon.closest('button, a, i').click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                await asyncio.sleep(1)
                logger.info("      ✅ Clicked search icon via JavaScript")
            except Exception as e:
                logger.warning(f"      ⚠️ JavaScript click failed: {str(e)}, trying Playwright...")
                # Fallback: try direct click
                await self._click_with_retry('i.glyphicon-search', "magnifying glass icon")
            
            # 4. Wait for modal to appear and type molecule name
            logger.info(f"      → Step 4: Typing '{molecule}'...")
            await self.page.wait_for_selector('input[ng-model="filter.nome"]', state='visible', timeout=10000)
            await self.page.fill('input[ng-model="filter.nome"]', molecule)
            await asyncio.sleep(0.5)
            
            # 5. Click "Pesquisar" button in the modal
            logger.info("      → Step 5: Clicking 'Pesquisar'...")
            await self._click_with_retry(
                'input[value="Pesquisar"][type="submit"]',
                "Pesquisar button"
            )
            await asyncio.sleep(2)
            
            # 6. Click checkbox/select icon for first result
            logger.info("      → Step 6: Selecting molecule from results...")
            await self.page.wait_for_selector('a:has(i.glyphicon-check)', state='visible', timeout=10000)
            await self.page.click('a:has(i.glyphicon-check)', timeout=5000)
            await asyncio.sleep(1)
            
            # 7. Click final "Consultar" button
            logger.info("      → Step 7: Clicking final 'Consultar'...")
            await self._click_with_retry(
                'input.btn-primary[value="Consultar"]',
                "final Consultar button"
            )
            await self._wait_for_angular()
            await asyncio.sleep(3)  # Wait for results
            
            # 8. Parse results
            products = await self._parse_results_table()
            
        except Exception as e:
            logger.warning(f"      ⚠️ Active ingredient search error: {str(e)}")
            # Take screenshot for debugging
            try:
                screenshot_path = f"/tmp/anvisa_error_{molecule}.png"
                await self.page.screenshot(path=screenshot_path)
                logger.info(f"      📸 Screenshot saved: {screenshot_path}")
            except:
                pass
        
        return products
    
    async def _parse_results_table(self) -> List[Dict]:
        """
        Parse results table and click through to get details
        """
        products = []
        
        try:
            # Get page HTML
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all clickable product rows
            # Looking for td with ng-click="detail(produto)"
            rows = soup.find_all('td', {'ng-click': lambda x: x and 'detail' in x})
            
            logger.info(f"      → Found {len(rows)} result rows")
            
            if not rows:
                return products
            
            # Click through each result (limit to 20 to avoid timeout)
            for i, row in enumerate(rows[:20]):
                try:
                    product_name = row.get_text(strip=True)
                    logger.info(f"      → [{i+1}/{min(len(rows), 20)}] Clicking: {product_name}...")
                    
                    # Click the row
                    await self.page.click(f'td:has-text("{product_name}")', timeout=10000)
                    await asyncio.sleep(2)  # Wait for detail page
                    
                    # Parse product details
                    product = await self._parse_product_details()
                    if product:
                        products.append(product)
                        logger.info(f"         ✅ Parsed: {product.get('product_name', 'Unknown')}")
                    
                    # Go back to results
                    await self.page.go_back()
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"         ⚠️ Error parsing product {i+1}: {str(e)}")
                    # Try to go back if stuck
                    try:
                        await self.page.go_back()
                        await asyncio.sleep(1)
                    except:
                        pass
            
        except Exception as e:
            logger.warning(f"      ⚠️ Table parsing error: {str(e)}")
        
        return products
    
    async def _parse_product_details(self) -> Optional[Dict]:
        """
        Parse product detail page
        Extract all fields from the detail view
        """
        try:
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Build product dict
            product = {}
            
            # Helper function to find value by label
            def find_value_by_label(label_text: str) -> str:
                label = soup.find(string=lambda x: x and label_text in x)
                if label:
                    parent = label.find_parent()
                    if parent:
                        # Try next sibling
                        next_td = parent.find_next_sibling()
                        if next_td:
                            value = next_td.get_text(strip=True)
                            # Ignore values that look like labels (headers)
                            label_keywords = ['Número', 'Data', 'Empresa', 'Categoria', 'Medicamento', 
                                            'Classe', 'Tipo', 'Complemento', 'Princípio', 'Vencimento',
                                            'Situação', 'Regularização']
                            is_header = any(kw in value for kw in label_keywords) and len(value) > 10
                            if not is_header:
                                return value
                return ""
            
            # Extract all fields
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
            
            # Try to find presentations table
            presentations = []
            # Look for table with Nº, Apresentação, Registro, etc.
            # This would need more detailed parsing
            product['presentations'] = presentations
            
            # Only return if we got minimum data
            if product.get('product_name') and product.get('active_ingredient'):
                return product
            else:
                return None
                
        except Exception as e:
            logger.warning(f"         ⚠️ Detail parsing error: {str(e)}")
            return None
    
    def _build_summary(self, products: List[Dict]) -> Dict:
        """Build summary statistics"""
        if not products:
            return {
                'total_products': 0,
                'first_approval': None,
                'reference_drugs': 0,
                'generic_drugs': 0,
                'companies': []
            }
        
        # Analyze products
        reference_count = 0
        generic_count = 0
        companies = set()
        dates = []
        
        for p in products:
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
            # Parse dates (format: DD/MM/YYYY)
            try:
                parsed_dates = []
                for d in dates:
                    parts = d.split('/')
                    if len(parts) == 3:
                        # Convert to YYYY-MM-DD for sorting
                        parsed_dates.append(f"{parts[2]}-{parts[1]}-{parts[0]}")
                if parsed_dates:
                    first_date = min(parsed_dates)
            except:
                pass
        
        return {
            'total_products': len(products),
            'first_approval': first_date,
            'reference_drugs': reference_count,
            'generic_drugs': generic_count,
            'companies': sorted(list(companies))
        }


# Singleton instance
anvisa_crawler = AnvisaCrawler()
