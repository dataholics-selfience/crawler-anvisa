"""
ANVISA Crawler v2.3 - STATUS-BASED NAVIGATION

NOVA ESTRATÉGIA baseada em dica do usuário:
✅ Cada resultado tem campo "Ativo" ou "Inativo"
✅ Esse campo identifica UNIVOCAMENTE cada medicamento
✅ Usar esse campo como âncora para navegação

APPROACH:
1. Encontrar todas as células com texto "Ativo" ou "Inativo"
2. Para cada uma dessas células (= 1 medicamento)
3. Clicar na PRIMEIRA célula da mesma linha (nome do produto)
4. Parse e voltar

MAINTAINS:
✅ Playwright v1.48.0
✅ Same proxy rotation
✅ Same stealth techniques
"""

import asyncio
import logging
import re
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger("anvisa")

# Same proxies
PROXIES = [
    "http://brd-customer-hl_8ea11d75-zone-residential_proxy1:w7qs41l7ijfc@brd.superproxy.io:33335",
    "http://brd-customer-hl_8ea11d75-zone-datacenter_proxy1:93u1xg5fef4p@brd.superproxy.io:33335",
    "http://5SHQXNTHNKDHUHFD:wifi;us;;;@proxy.scrapingbee.com:8886",
    "http://XNK2KLGACMN0FKRY:wifi;us;;;@proxy.scrapingbee.com:8886",
]


class AnvisaCrawlerV2:
    """Anvisa Crawler - Status-Based Navigation"""
    
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
        Search Anvisa for drug registrations
        
        Args:
            molecule: Molecule name
            brand: Brand name (optional)
            groq_api_key: Groq API key for translation
            use_proxy: Use proxy rotation
        
        Returns:
            Dict with found products and summary
        """
        logger.info("=" * 100)
        logger.info(f"🏥 ANVISA SEARCH V2.3 (STATUS-BASED): {molecule}" + (f" ({brand})" if brand else ""))
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
                # Launch browser
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
                
                # Strategy 1: Try brand name search
                if brand_pt:
                    logger.info(f"   🔍 Strategy 1: Searching by brand name '{brand_pt}'...")
                    products = await self._search_by_brand_name(brand_pt)
                    if products:
                        logger.info(f"      ✅ Found {len(products)} products via brand name")
                        all_products.extend(products)
                
                # Strategy 2: Search by active ingredient
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
        logger.info(f"✅ V2.3 Search completed: {len(all_products)} products found")
        
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
        """Search by brand name"""
        products = []
        
        try:
            url = f"https://consultas.anvisa.gov.br/#/medicamentos/q/?nomeProduto={brand_name}"
            logger.info(f"      → URL: {url}")
            
            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(3)
            
            # Try pagination
            await self._set_pagination_50()
            
            # Parse using STATUS-BASED method
            products = await self._parse_results_table_status_based()
            
        except Exception as e:
            logger.warning(f"      ⚠️ Brand name search error: {str(e)}")
        
        return products
    
    async def _search_by_active_ingredient(self, molecule: str) -> List[Dict]:
        """Search by active ingredient - ADVANCED SEARCH"""
        products = []
        
        try:
            # 1. Main page
            logger.info("      → Step 1: Going to main page...")
            await self.page.goto(
                "https://consultas.anvisa.gov.br/#/medicamentos/",
                wait_until='networkidle',
                timeout=60000
            )
            await asyncio.sleep(3)
            
            # 2. Click "Busca Avançada" with multiple selectors
            logger.info("      → Step 2: Clicking 'Busca Avançada'...")
            
            clicked = False
            selectors = [
                'input[value="Busca Avançada"]',
                'input[ng-click="toggleBuscaAvancada()"]',
                'button:has-text("Busca Avançada")',
                '.btn-default:has-text("Busca")'
            ]
            
            for selector in selectors:
                try:
                    await self.page.click(selector, timeout=5000)
                    clicked = True
                    logger.info(f"         ✅ Clicked: {selector}")
                    break
                except Exception as e:
                    logger.debug(f"         → Failed {selector}: {str(e)}")
                    continue
            
            if not clicked:
                logger.warning("      ⚠️ Could not click Busca Avançada")
                # Continue anyway - might already be in advanced mode
            
            await asyncio.sleep(2)
            
            # 3. Click search icon
            logger.info("      → Step 3: Opening molecule search...")
            await self.page.click('i.glyphicon-search', timeout=10000)
            await asyncio.sleep(1)
            
            # 4. Type molecule
            logger.info(f"      → Step 4: Typing '{molecule}'...")
            await self.page.fill('input[ng-model="filter.nome"]', molecule)
            await asyncio.sleep(1)
            
            # 5. Click Pesquisar
            logger.info("      → Step 5: Clicking 'Pesquisar'...")
            await self.page.click('input[value="Pesquisar"][type="submit"]', timeout=10000)
            await asyncio.sleep(2)
            
            # 6. Select first result
            logger.info("      → Step 6: Selecting molecule...")
            await self.page.click('a:has(i.glyphicon-check)', timeout=10000)
            await asyncio.sleep(1)
            
            # 7. Click Consultar
            logger.info("      → Step 7: Clicking 'Consultar'...")
            await self.page.click('input.btn-primary[value="Consultar"]', timeout=10000)
            await asyncio.sleep(3)
            
            # 8. Pagination
            await self._set_pagination_50()
            
            # 9. Parse using STATUS-BASED method
            products = await self._parse_results_table_status_based()
            
        except Exception as e:
            logger.warning(f"      ⚠️ Active ingredient search error: {str(e)}")
        
        return products
    
    async def _set_pagination_50(self):
        """Set pagination to 50"""
        try:
            await self.page.wait_for_selector('table tbody tr', timeout=5000)
            await asyncio.sleep(1)
            
            button_exists = await self.page.evaluate("""
                Array.from(document.querySelectorAll('button')).some(b => b.textContent.trim() === '50')
            """)
            
            if button_exists:
                logger.info("      → Clicking 50 results button...")
                await self.page.click('button:has-text("50")', timeout=5000)
                await asyncio.sleep(3)
                logger.info("      → Pagination set to 50")
            else:
                logger.info("      → Pagination not needed")
                
        except Exception as e:
            logger.debug(f"      → Pagination: {str(e)}")
    
    async def _parse_results_table_status_based(self) -> List[Dict]:
        """
        NEW: Parse using "Ativo/Inativo" status field as unique identifier
        
        Strategy based on user tip:
        1. Find all cells containing "Ativo" or "Inativo"
        2. Each one = 1 unique product
        3. For each status cell, find first clickable cell in same row
        4. Click that cell to open product details
        """
        products = []
        
        try:
            # Wait for table
            await self.page.wait_for_selector('table', timeout=10000)
            await asyncio.sleep(2)
            
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all cells with "Ativo" or "Inativo" text
            # This identifies each unique product
            status_cells = soup.find_all('td', string=lambda text: text and (text.strip() == 'Ativo' or text.strip() == 'Inativo'))
            
            logger.info(f"      → Found {len(status_cells)} products (by Ativo/Inativo status)")
            
            if not status_cells:
                logger.warning("      → No status cells found - trying alternative detection")
                # Fallback: find cells with text containing these words
                status_cells = soup.find_all('td', string=lambda text: text and ('Ativo' in text or 'Inativo' in text))
                logger.info(f"      → Fallback found {len(status_cells)} cells")
            
            if not status_cells:
                logger.error("      → No products detected in results table")
                return products
            
            # Process each product
            max_products = min(len(status_cells), 50)
            
            for idx in range(max_products):
                try:
                    # Re-get page content
                    await asyncio.sleep(1)
                    html = await self.page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Re-find status cells
                    status_cells_refresh = soup.find_all('td', string=lambda text: text and (text.strip() == 'Ativo' or text.strip() == 'Inativo'))
                    
                    if not status_cells_refresh:
                        status_cells_refresh = soup.find_all('td', string=lambda text: text and ('Ativo' in text or 'Inativo' in text))
                    
                    if idx >= len(status_cells_refresh):
                        logger.warning(f"      → Product {idx} no longer in results")
                        break
                    
                    status_cell = status_cells_refresh[idx]
                    status_text = status_cell.get_text(strip=True)
                    
                    # Find the parent row of this status cell
                    parent_row = status_cell.find_parent('tr')
                    
                    if not parent_row:
                        logger.warning(f"      → [{idx+1}] No parent row for status cell")
                        continue
                    
                    # Find first clickable cell in this row
                    first_clickable = parent_row.find('td', {'ng-click': lambda x: x and 'detail' in x})
                    
                    if not first_clickable:
                        logger.warning(f"      → [{idx+1}] No clickable cell in row")
                        continue
                    
                    product_name = first_clickable.get_text(strip=True)
                    logger.info(f"      → [{idx+1}/{max_products}] Clicking: {product_name} ({status_text})...")
                    
                    # Click using JavaScript
                    # Strategy: Find status cells again, get parent row, click first cell
                    js_click = f"""
                    (function() {{
                        // Find all status cells
                        var allCells = Array.from(document.querySelectorAll('td'));
                        var statusCells = allCells.filter(function(cell) {{
                            var text = cell.textContent.trim();
                            return text === 'Ativo' || text === 'Inativo';
                        }});
                        
                        if (statusCells.length === 0) {{
                            // Fallback: partial match
                            statusCells = allCells.filter(function(cell) {{
                                var text = cell.textContent;
                                return text.indexOf('Ativo') !== -1 || text.indexOf('Inativo') !== -1;
                            }});
                        }}
                        
                        if (!statusCells[{idx}]) {{
                            return false;
                        }}
                        
                        // Get parent row
                        var row = statusCells[{idx}].closest('tr');
                        if (!row) {{
                            return false;
                        }}
                        
                        // Find first clickable cell in this row
                        var clickable = row.querySelector('td[ng-click*="detail"]');
                        if (clickable) {{
                            clickable.click();
                            return true;
                        }}
                        
                        return false;
                    }})()
                    """
                    
                    clicked = await self.page.evaluate(js_click)
                    
                    if not clicked:
                        logger.warning(f"         ⚠️ Could not click product {idx+1}")
                        continue
                    
                    # Wait for details page
                    await asyncio.sleep(3)
                    
                    try:
                        await self.page.wait_for_selector('table', timeout=15000)
                    except:
                        logger.warning(f"         ⚠️ Details page timeout for {product_name}")
                        await self.page.go_back(timeout=5000)
                        await asyncio.sleep(2)
                        continue
                    
                    # Parse product
                    product = await self._parse_product_details_v2()
                    
                    if product:
                        products.append(product)
                        logger.info(f"         ✅ Parsed: {product.get('product_name', 'Unknown')}")
                        pres_count = len(product.get('presentations', []))
                        links = product.get('links', {})
                        logger.info(f"            → Presentations: {pres_count}, "
                                  f"Bulário: {bool(links.get('bulario'))}, "
                                  f"Parecer: {bool(links.get('parecer_publico'))}, "
                                  f"Rotulagem: {len(links.get('rotulagem', []))}")
                    
                    # Go back
                    await self.page.go_back()
                    await asyncio.sleep(2)
                    
                    try:
                        await self.page.wait_for_selector('table', timeout=10000)
                    except:
                        logger.warning(f"         ⚠️ Results page reload timeout")
                        break
                    
                except PlaywrightTimeout:
                    logger.warning(f"         ⚠️ Timeout on product {idx+1}")
                    try:
                        await self.page.go_back(timeout=5000)
                        await asyncio.sleep(2)
                    except:
                        pass
                        
                except Exception as e:
                    logger.warning(f"         ⚠️ Error on product {idx+1}: {str(e)}")
                    try:
                        await self.page.go_back(timeout=5000)
                        await asyncio.sleep(2)
                    except:
                        pass
            
        except Exception as e:
            logger.error(f"      ⚠️ Table parsing error: {str(e)}")
            import traceback
            logger.debug(f"      → Traceback: {traceback.format_exc()}")
        
        return products
    
    async def _parse_product_details_v2(self) -> Optional[Dict]:
        """Parse product detail page"""
        try:
            html = await self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            product = {}
            
            def find_value_by_label(label_text: str) -> str:
                label = soup.find(string=lambda x: x and label_text in x)
                if label:
                    parent = label.find_parent()
                    if parent:
                        next_td = parent.find_next_sibling()
                        if next_td:
                            value = next_td.get_text(strip=True)
                            label_keywords = ['Número', 'Data', 'Empresa', 'Categoria', 'Medicamento', 
                                            'Classe', 'Tipo', 'Complemento', 'Princípio', 'Vencimento',
                                            'Situação', 'Regularização']
                            is_header = any(kw in value for kw in label_keywords) and len(value) > 10
                            if not is_header:
                                return value
                return ""
            
            # Extract fields
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
            
            product['links'] = self._extract_document_links(soup)
            product['presentations'] = self._extract_presentations(soup)
            
            if product.get('product_name') and product.get('active_ingredient'):
                return product
            else:
                return None
                
        except Exception as e:
            logger.warning(f"         ⚠️ Detail parsing error: {str(e)}")
            return None
    
    def _extract_document_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract document links"""
        links = {
            'bulario': '',
            'parecer_publico': '',
            'rotulagem': []
        }
        
        try:
            # Bulário
            bulario_label = soup.find(string=lambda x: x and 'Bulário Eletrônico' in x)
            if bulario_label:
                parent = bulario_label.find_parent()
                if parent:
                    next_td = parent.find_next_sibling()
                    if next_td:
                        link = next_td.find('a')
                        if link and link.get('href'):
                            links['bulario'] = link.get('href')
            
            # Parecer
            parecer_label = soup.find(string=lambda x: x and 'Parecer Público' in x)
            if parecer_label:
                parent = parecer_label.find_parent()
                if parent:
                    next_td = parent.find_next_sibling()
                    if next_td:
                        link = next_td.find('a')
                        if link and link.get('href'):
                            links['parecer_publico'] = link.get('href')
            
            # Rotulagem
            rotulagem_label = soup.find(string=lambda x: x and 'Rotulagem' in x)
            if rotulagem_label:
                parent = rotulagem_label.find_parent()
                if parent:
                    next_td = parent.find_next_sibling()
                    if next_td:
                        all_links = next_td.find_all('a')
                        for link in all_links:
                            if link.get_text(strip=True):
                                links['rotulagem'].append({
                                    'filename': link.get_text(strip=True),
                                    'url': link.get('href', '')
                                })
            
        except Exception as e:
            logger.debug(f"         → Error extracting links: {str(e)}")
        
        return links
    
    def _extract_presentations(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract presentations"""
        presentations = []
        
        try:
            tables = soup.find_all('table')
            
            for table in tables:
                headers = table.find_all('th')
                header_texts = [h.get_text(strip=True) for h in headers]
                
                if 'Apresentação' in str(header_texts) or 'Registro' in str(header_texts):
                    rows = table.find_all('tr')
                    
                    for row in rows[1:]:
                        cols = row.find_all('td')
                        
                        if len(cols) >= 5:
                            presentation = {
                                'number': cols[0].get_text(strip=True) if len(cols) > 0 else '',
                                'description': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                                'registration': cols[2].get_text(strip=True) if len(cols) > 2 else '',
                                'pharmaceutical_form': cols[3].get_text(strip=True) if len(cols) > 3 else '',
                                'publication_date': cols[4].get_text(strip=True) if len(cols) > 4 else '',
                                'validity': cols[5].get_text(strip=True) if len(cols) > 5 else ''
                            }
                            
                            if presentation['description']:
                                presentations.append(presentation)
                    
                    break
            
        except Exception as e:
            logger.debug(f"         → Error extracting presentations: {str(e)}")
        
        return presentations
    
    def _build_summary(self, products: List[Dict]) -> Dict:
        """Build summary"""
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
        
        reference_count = 0
        generic_count = 0
        companies = set()
        dates = []
        total_presentations = 0
        bulario_count = 0
        parecer_count = 0
        rotulagem_count = 0
        
        for p in products:
            total_presentations += len(p.get('presentations', []))
            
            links = p.get('links', {})
            if links.get('bulario'):
                bulario_count += 1
            if links.get('parecer_publico'):
                parecer_count += 1
            if links.get('rotulagem'):
                rotulagem_count += 1
            
            if p.get('reference_drug'):
                if 'REFERÊNCIA' in p['reference_drug'].upper():
                    reference_count += 1
                elif 'GENÉRICO' in p['reference_drug'].upper():
                    generic_count += 1
            
            if p.get('company'):
                companies.add(p['company'])
            
            if p.get('registration_date'):
                dates.append(p['registration_date'])
        
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


# Singleton
anvisa_crawler_v2 = AnvisaCrawlerV2()
