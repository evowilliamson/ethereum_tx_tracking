/**
 * DeFiLlama Yields Data Fetcher
 * Fetches all yield/APY data for all coins from DeFiLlama API
 * 
 * No API key required - DeFiLlama API is free and public
 * 
 * Usage:
 * 1. Open Google Sheets
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code
 * 4. Refresh the sheet to see the custom menu
 * 5. Use the "DeFi Yields" menu to access all functions
 */

/**
 * Creates a custom menu when the spreadsheet is opened
 * This menu provides easy access to all functions without needing drawing buttons
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('DeFiLlama')
    .addItem('Get Yields', 'getDefiLlamaYields')
    .addItem('Show All', 'showAllYields')
    .addItem('Show Followed', 'showFollowedYields')
    .addSeparator()
    .addItem('Copy to Historical', 'copyToHistorical')
    .addToUi();
}

function getDefiLlamaYields() {
  // DeFiLlama API endpoints (no API key required)
  const YIELDS_ENDPOINT = 'https://yields.llama.fi/pools';
  const PROTOCOLS_ENDPOINT = 'https://api.llama.fi/protocols';
  
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  try {
    // Show starting toast
    spreadsheet.toast('Starting to fetch yield pools from DeFiLlama...', 'Fetching Yields', 2);
    
    // Fetch all yield pools
    Logger.log('Fetching yield pools from DeFiLlama...');
    const yieldsResponse = UrlFetchApp.fetch(YIELDS_ENDPOINT);
    const yieldsData = JSON.parse(yieldsResponse.getContentText());
    
    // Debug: Log response structure
    Logger.log('Response type: ' + typeof yieldsData);
    Logger.log('Is array: ' + Array.isArray(yieldsData));
    if (yieldsData && typeof yieldsData === 'object') {
      Logger.log('Response keys: ' + Object.keys(yieldsData).join(', '));
      if (yieldsData.data) {
        Logger.log('Data array length: ' + (Array.isArray(yieldsData.data) ? yieldsData.data.length : 'N/A'));
      }
    }
    
    // Fetch protocol information (optional, for better context)
    Logger.log('Fetching protocol information...');
    let protocolsMap = {};
    try {
      const protocolsResponse = UrlFetchApp.fetch(PROTOCOLS_ENDPOINT);
      const protocolsData = JSON.parse(protocolsResponse.getContentText());
      protocolsData.forEach(protocol => {
        protocolsMap[protocol.name] = protocol;
      });
    } catch (e) {
      Logger.log('Could not fetch protocols: ' + e);
    }
    
    // Get active sheet and verify it's the "Current" sheet
    let sheet = SpreadsheetApp.getActiveSheet();
    if (sheet.getName() !== 'Current') {
      Logger.log(`Active sheet is "${sheet.getName()}", switching to "Current" for data operations`);
      sheet = spreadsheet.getSheetByName('Current');
    }
    
    if (!sheet) {
      spreadsheet.toast('Error: "Current" sheet not found!', 'Fetching Yields', 5);
      return;
    }
    
    // Save column widths before any operations to preserve user's formatting
    const lastCol = sheet.getLastColumn();
    const savedColumnWidths = [];
    if (lastCol > 0) {
      for (let col = 1; col <= lastCol; col++) {
        savedColumnWidths[col - 1] = sheet.getColumnWidth(col);
      }
      Logger.log(`Saved column widths for ${lastCol} columns from sheet "${sheet.getName()}"`);
    }
    
    // Match existing Pool IDs to preserve Coin and Tracing status (read column A = Pool ID, column B = Coin, column C = Tracing)
    const coinMap = {};
    const tracingStatusMap = {};
    const lastRow = sheet.getLastRow();
    let actualLastDataRow = 4; // Start with header row
    
    if (lastRow > 4) {
      // Read columns A (Pool ID), B (Coin), C (Tracing), skip header row (row 4), start from row 5
      // Important: read from the "Current" sheet specifically
      const existingData = sheet.getRange(5, 1, lastRow - 4, 3).getValues();
      existingData.forEach((row, index) => {
        const poolId = row[0] || '';
        const coin = String(row[1] || '').trim();  // Column B: Coin
        const tracingStatus = String(row[2] || '').trim();  // Column C: Tracing
        if (poolId) {
          coinMap[poolId] = coin;
          tracingStatusMap[poolId] = tracingStatus;
          // Track the actual last row with data (row 5 + index)
          actualLastDataRow = 5 + index;
        }
      });
      Logger.log(`Found ${Object.keys(tracingStatusMap).length} existing Pool IDs to match in sheet "${sheet.getName()}"`);
    }
    
    // Delete all rows from row 5 onwards (preserve rows 1-4: headers and filters)
    // This removes empty rows from table view
    // Keep deleting until we only have rows 1-4 left
    while (sheet.getLastRow() > 4) {
      const currentLastRow = sheet.getLastRow();
      const numRowsToDelete = currentLastRow - 4;
      // Delete all data rows at once (row 5 to currentLastRow)
      // deleteRows(startRow, numRows) - deletes numRows starting from startRow (1-indexed)
      sheet.deleteRows(5, numRowsToDelete);
      Logger.log(`Deleted ${numRowsToDelete} rows starting from row 5 (last row was ${currentLastRow})`);
    }
    
    // Headers array for column count (headers are already in row 4, don't overwrite)
    const headers = [
      'Pool ID',
      'Coin',
      'Tracing',
      'Chain',
      'Project',
      'Symbol',
      'TVL (USD)',
      'APY',
      'APY Base',
      'APY Reward',
      'Pool Meta'
    ];
    
    // Process and write data
    const rows = [];
    
    // DeFiLlama API returns an object with 'data' array, not direct array
    let poolsArray = [];
    if (Array.isArray(yieldsData)) {
      poolsArray = yieldsData;
    } else if (yieldsData && Array.isArray(yieldsData.data)) {
      poolsArray = yieldsData.data;
    } else if (yieldsData && typeof yieldsData === 'object') {
      // Try to find array in response
      for (let key in yieldsData) {
        if (Array.isArray(yieldsData[key])) {
          poolsArray = yieldsData[key];
          break;
        }
      }
    }
    
    // Show toast notification with total rows to process
    if (poolsArray.length > 0) {
      spreadsheet.toast(`Processing ${poolsArray.length.toLocaleString()} yield pools...`, 'Fetching Yields', 3);
    }
    
    // Store data rows with Pool ID in column A, Coin in column B, Tracing in column C
    const dataRows = [];
    
    if (poolsArray.length > 0) {
      poolsArray.forEach(pool => {
        const poolId = pool.pool || '';
        // Match existing Pool ID to preserve Coin and Tracing status
        const coin = coinMap[poolId] || '';  // Preserve existing Coin, empty for new pools
        const tracingStatus = tracingStatusMap[poolId] || 'Don\'t follow';
        
        // Format TVL
        const tvl = pool.tvlUsd ? pool.tvlUsd.toFixed(2) : '';
        
        // Format APY values
        const apy = pool.apy ? (pool.apy * 100).toFixed(2) + '%' : '';
        const apyBase = pool.apyBase ? (pool.apyBase * 100).toFixed(2) + '%' : '';
        const apyReward = pool.apyReward ? (pool.apyReward * 100).toFixed(2) + '%' : '';
        
        // Store data starting at column A: Pool ID, Coin, Tracing, then Chain, Project, etc.
        dataRows.push([
          poolId,        // Column A: Pool ID
          coin,          // Column B: Coin (preserved from existing data, empty for new pools)
          tracingStatus, // Column C: Tracing (Follow/Don't follow)
          pool.chain || '',      // Column D: Chain
          pool.project || '',    // Column E: Project
          pool.symbol || '',     // Column F: Symbol
          tvl,                   // Column G: TVL (USD)
          apy,                   // Column H: APY
          apyBase,               // Column I: APY Base
          apyReward,             // Column J: APY Reward
          pool.poolMeta || ''    // Column K: Pool Meta
        ]);
      });
    }
    
    Logger.log(`Built ${dataRows.length} data rows from ${poolsArray.length} pools`);
    if (dataRows.length > 0) {
      Logger.log(`First row sample: Pool ID=${dataRows[0][0]}, Coin=${dataRows[0][1]}, Tracing=${dataRows[0][2]}, Chain=${dataRows[0][3]}, Symbol=${dataRows[0][5]}`);
    }
    
    // Read filter configuration from Current sheet (rows 2-3)
    // Filters align with data columns: A=Pool ID, B=Coin, C=Tracing, D=Chain, E=Project, F=Symbol, G=TVL, H=APY, I=APY Base, J=APY Reward, K=Pool Meta
    // Filter cells: C3=Tracing, D3=Chain, E3=Project, F3=Symbol, G=TVL, H=APY, I=Base, J=Reward, K=Meta
    const tracingFilter = String(sheet.getRange('C3').getValue() || '').trim();
    const chainFilter = String(sheet.getRange('D3').getValue() || '').trim();
    const projectFilter = String(sheet.getRange('E3').getValue() || '').trim();
    const symbolFilter = String(sheet.getRange('F3').getValue() || '').trim();
    
    // Helper to check if a filter value is "All" or empty
    const isAllValue = (val) => !val || val.trim().toLowerCase() === 'all';
    
    // Read range filters (min from row 2, max from row 3)
    const tvlMinRaw = sheet.getRange('G2').getValue();
    const tvlMaxRaw = sheet.getRange('G3').getValue();
    const apyMinRaw = sheet.getRange('H2').getValue();
    const apyMaxRaw = sheet.getRange('H3').getValue();
    const apyBaseMinRaw = sheet.getRange('I2').getValue();
    const apyBaseMaxRaw = sheet.getRange('I3').getValue();
    const apyRewardMinRaw = sheet.getRange('J2').getValue();
    const apyRewardMaxRaw = sheet.getRange('J3').getValue();
    const poolMetaMinRaw = sheet.getRange('K2').getValue();
    const poolMetaMaxRaw = sheet.getRange('K3').getValue();
    
    // Convert to numbers (handle empty strings, percentages, currency)
    const tvlMin = parseFilterValue(tvlMinRaw);
    const tvlMax = parseFilterValue(tvlMaxRaw);
    const apyMin = parseFilterValue(apyMinRaw);
    const apyMax = parseFilterValue(apyMaxRaw);
    const apyBaseMin = parseFilterValue(apyBaseMinRaw);
    const apyBaseMax = parseFilterValue(apyBaseMaxRaw);
    const apyRewardMin = parseFilterValue(apyRewardMinRaw);
    const apyRewardMax = parseFilterValue(apyRewardMaxRaw);
    const poolMetaMin = parseFilterValue(poolMetaMinRaw);
    const poolMetaMax = parseFilterValue(poolMetaMaxRaw);
    
    // Parse comma-separated filter values (convert to arrays, trim, lowercase for wildcard matching)
    // Treat "All" as an empty filter array (show all)
    const chainFilters = isAllValue(chainFilter) ? [] : chainFilter.split(',').map(s => String(s).trim().toLowerCase()).filter(s => s.length > 0);
    const projectFilters = isAllValue(projectFilter) ? [] : projectFilter.split(',').map(s => String(s).trim().toLowerCase()).filter(s => s.length > 0);
    const symbolFilters = isAllValue(symbolFilter) ? [] : symbolFilter.split(',').map(s => String(s).trim().toLowerCase()).filter(s => s.length > 0);
    
    Logger.log(`Using sheet "${sheet.getName()}" for filters`);
    Logger.log('Current sheet filters: Tracing=' + tracingFilter + ', Chain=' + chainFilter + ', Project=' + projectFilter + ', Symbol=' + symbolFilter);
    Logger.log('Total data rows to filter: ' + dataRows.length);
    Logger.log('Chain filters array: [' + chainFilters.join(', ') + ']');
    Logger.log('Symbol filters array: [' + symbolFilters.join(', ') + ']');
    
    // Apply filters to data rows
    const filteredDataRows = [];
    let debugCount = 0;
    
    dataRows.forEach((row, index) => {
      debugCount++;
      const poolId = String(row[0] || '').trim();
      const tracingStatus = String(row[2] || '').trim();  // Column C (index 2) - Tracing
      const chain = String(row[3] || '').trim();  // Column D (index 3) - Chain
      const project = String(row[4] || '').trim(); // Column E (index 4) - Project
      const symbol = String(row[5] || '').trim();  // Column F (index 5) - Symbol
      const tvl = parseFloat(row[6]) || 0;  // Column G (index 6) - TVL (USD)
      
      // Parse APY values
      const apyStr = String(row[7] || '').replace('%', '').trim();
      const apyIsEmpty = !row[7] || apyStr === '' || isNaN(parseFloat(apyStr));
      const apy = apyIsEmpty ? null : (parseFloat(apyStr) || 0);
      
      const apyBaseStr = String(row[8] || '').replace('%', '').trim();
      const apyBaseIsEmpty = !row[8] || apyBaseStr === '' || isNaN(parseFloat(apyBaseStr));
      const apyBase = apyBaseIsEmpty ? null : (parseFloat(apyBaseStr) || 0);
      
      const apyRewardStr = String(row[9] || '').replace('%', '').trim();
      const apyRewardIsEmpty = !row[9] || apyRewardStr === '' || isNaN(parseFloat(apyRewardStr));
      const apyReward = apyRewardIsEmpty ? null : (parseFloat(apyRewardStr) || 0);
      
      const poolMetaStr = String(row[10] || '').trim();
      const poolMetaIsEmpty = !row[10] || poolMetaStr === '' || isNaN(parseFloat(poolMetaStr));
      const poolMeta = poolMetaIsEmpty ? null : (parseFloat(poolMetaStr) || 0);
      
      // Apply filters
      let passesFilter = true;
      let failReason = "";
      
      // Tracing filter
      if (tracingFilter && tracingFilter.trim().toLowerCase() !== 'all' && passesFilter) {
        const tracingFilterLower = tracingFilter.trim().toLowerCase();
        if (tracingFilterLower === 'follow') {
          if (tracingStatus !== 'Follow') { passesFilter = false; failReason = "Tracing!=Follow"; }
        } else if (tracingFilterLower === 'don\'t follow' || tracingFilterLower === 'dont follow') {
          if (tracingStatus !== 'Don\'t follow') { passesFilter = false; failReason = "Tracing!=Don't follow"; }
        }
      }
      
      // Chain filter
      if (passesFilter && chainFilters.length > 0) {
        const chainLower = chain.toLowerCase();
        if (!chainFilters.some(f => chainLower.includes(f))) {
          passesFilter = false;
          failReason = "Chain mismatch (" + chain + ")";
        }
      }
      
      // Project filter
      if (passesFilter && projectFilters.length > 0) {
        const projectLower = project.toLowerCase();
        if (!projectFilters.some(f => projectLower.includes(f))) {
          passesFilter = false;
          failReason = "Project mismatch (" + project + ")";
        }
      }
      
      // Symbol filter
      if (passesFilter && symbolFilters.length > 0) {
        const symbolLower = symbol.toLowerCase();
        if (!symbolFilters.some(f => symbolLower.includes(f))) {
          passesFilter = false;
          failReason = "Symbol mismatch (" + symbol + ")";
        }
      }
      
      // Range filters
      if (passesFilter) {
        if (tvlMin != null && tvl < tvlMin) { passesFilter = false; failReason = "TVL too low (" + tvl + ")"; }
        if (passesFilter && tvlMax != null && tvl > tvlMax) { passesFilter = false; failReason = "TVL too high (" + tvl + ")"; }
        
        if (passesFilter && !apyIsEmpty) {
          if (apyMin != null && apy < apyMin) { passesFilter = false; failReason = "APY too low (" + apy + ")"; }
          if (passesFilter && apyMax != null && apy > apyMax) { passesFilter = false; failReason = "APY too high (" + apy + ")"; }
        }
        
        if (passesFilter && !apyBaseIsEmpty) {
          if (apyBaseMin != null && apyBase < apyBaseMin) { passesFilter = false; failReason = "Base APY too low"; }
          if (passesFilter && apyBaseMax != null && apyBase > apyBaseMax) { passesFilter = false; failReason = "Base APY too high"; }
        }
        
        if (passesFilter && !apyRewardIsEmpty) {
          if (apyRewardMin != null && apyReward < apyRewardMin) { passesFilter = false; failReason = "Reward APY too low"; }
          if (passesFilter && apyRewardMax != null && apyReward > apyRewardMax) { passesFilter = false; failReason = "Reward APY too high"; }
        }
        
        if (passesFilter && !poolMetaIsEmpty) {
          if (poolMetaMin != null && poolMeta < poolMetaMin) { passesFilter = false; failReason = "Pool Meta too low"; }
          if (passesFilter && poolMetaMax != null && poolMeta > poolMetaMax) { passesFilter = false; failReason = "Pool Meta too high"; }
        }
      }
      
      // Log details for the first 20 rows to see what's happening
      if (debugCount <= 20) {
        Logger.log(`Row ${debugCount} [${poolId}]: Tracing="${tracingStatus}", Chain="${chain}", Symbol="${symbol}", TVL=${tvl} -> ${passesFilter ? "PASS" : "FAIL (" + failReason + ")"}`);
      }
      
      if (passesFilter) {
        filteredDataRows.push(row);
      }
    });
    
    Logger.log(`Filtered ${filteredDataRows.length} rows from ${dataRows.length} total rows`);
    if (filteredDataRows.length === 0 && dataRows.length > 0) {
      Logger.log('WARNING: All rows were filtered out! Check filter criteria.');
    }
    
    Logger.log(`Filtered ${filteredDataRows.length} rows from ${dataRows.length} total rows`);
    if (filteredDataRows.length === 0 && dataRows.length > 0) {
      Logger.log('WARNING: All rows were filtered out! Check filter criteria.');
    }
    
    // Create combined array with Tracing status and data for sorting
    const combinedRows = filteredDataRows.map((row) => ({
      tracingStatus: String(row[2] || '').trim(),  // Column C: Tracing
      tvl: parseFloat(row[6]) || 0,  // Column G: TVL for sorting
      data: row
    }));
    
    // Sort: First by Tracing (Follow first), then by TVL ascending (smallest TVL first)
    combinedRows.sort((a, b) => {
      // Primary sort: Tracing status - Follow first, then Don't follow
      if (a.tracingStatus === 'Follow' && b.tracingStatus !== 'Follow') return -1;
      if (a.tracingStatus !== 'Follow' && b.tracingStatus === 'Follow') return 1;
      // Secondary sort: TVL ascending
      if (a.tvl !== b.tvl) {
        return a.tvl - b.tvl;
      }
      return 0;
    });
    
    // Write data to sheet
    // Batch write for large datasets to avoid timeout
    if (combinedRows.length > 0) {
      Logger.log(`Writing ${combinedRows.length} rows to sheet...`);
      const BATCH_SIZE = 5000;
      let writtenRows = 0;
      
      for (let i = 0; i < combinedRows.length; i += BATCH_SIZE) {
        const batch = combinedRows.slice(i, i + BATCH_SIZE);
        const startRow = 5 + i;  // Data starts at row 5
        
        // Write all data starting from column A (Pool ID, Tracing, Chain, Project, etc.)
        const dataBatch = batch.map(item => item.data);
        sheet.getRange(startRow, 1, batch.length, headers.length).setValues(dataBatch);
        
        writtenRows += batch.length;
        Logger.log(`Written ${writtenRows} / ${combinedRows.length} rows...`);
        
        // Show progress toast
        const progressPercent = Math.round((writtenRows / combinedRows.length) * 100);
        spreadsheet.toast(`Processed ${writtenRows.toLocaleString()} / ${combinedRows.length.toLocaleString()} rows (${progressPercent}%)`, 'Fetching Yields', 2);
        
        // Small delay to avoid hitting rate limits
        if (i + BATCH_SIZE < combinedRows.length) {
          Utilities.sleep(100);
        }
      }
      
      Logger.log(`Successfully wrote ${combinedRows.length} yield pools to sheet`);
      spreadsheet.toast(`Successfully wrote ${combinedRows.length.toLocaleString()} yield pools to sheet`, 'Fetching Yields - Complete', 5);
    } else {
      Logger.log('No yield data found');
      spreadsheet.toast('No yield data found', 'Fetching Yields', 3);
    }
    
    // Restore saved column widths to preserve user's formatting
    if (savedColumnWidths.length > 0) {
      Logger.log('Restoring column widths...');
      for (let col = 1; col <= savedColumnWidths.length; col++) {
        if (savedColumnWidths[col - 1] !== null && savedColumnWidths[col - 1] !== undefined) {
          sheet.setColumnWidth(col, savedColumnWidths[col - 1]);
        }
      }
      Logger.log(`Restored column widths for ${savedColumnWidths.length} columns`);
    }
    // Note: Filter creation is left to the user - we only filter the API data, not the sheet
    
    Logger.log('Done! Check your Google Sheet for the yield data.');
    
    // Final completion toast
    if (combinedRows.length > 0) {
      spreadsheet.toast(`Completed! ${combinedRows.length.toLocaleString()} yield pools processed.`, 'Fetching Yields - Finished', 5);
    }
    
  } catch (error) {
    Logger.log('Error fetching DeFiLlama yields: ' + error);
    spreadsheet.toast('Error: ' + error, 'Fetching Yields - Error', 5);
    SpreadsheetApp.getUi().alert('Error: ' + error);
  }
}

/**
 * Show All Yields - Removes filter to show all rows (no API calls, just filtering)
 */
function showAllYields() {
  try {
    const sheet = SpreadsheetApp.getActiveSheet();
    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();
    
    if (lastRow > 4 && lastCol > 0) {
      // Check if filter exists and remove it (this shows all rows)
      const filter = sheet.getFilter();
      
      if (filter) {
        filter.remove();
        Logger.log('Filter removed - showing all yields');
      } else {
        Logger.log('No filter active - all yields already visible');
      }
    }
  } catch (error) {
    Logger.log('Error in showAllYields: ' + error);
    SpreadsheetApp.getUi().alert('Error showing all yields: ' + error);
  }
}

/**
 * Show Followed Yields - Filters to show only rows where column C (Tracing) = "Follow" (no API calls, just filtering)
 */
function showFollowedYields() {
  try {
    const sheet = SpreadsheetApp.getActiveSheet();
    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();
    
    if (lastRow > 4 && lastCol > 0) {
      // Check if filter exists
      let filter = sheet.getFilter();
      
      if (!filter) {
        // Create filter if it doesn't exist (starting from header row 4)
        filter = sheet.getRange(4, 1, lastRow - 3, lastCol).createFilter();
      }
      
      // Get the filter criteria builder for column C (Tracing column)
      const criteria = SpreadsheetApp.newFilterCriteria()
        .whenTextEqualTo('Follow')
        .build();
      
      // Apply filter to column 3 (column C - Tracing)
      filter.setColumnFilterCriteria(3, criteria);
      
      Logger.log('Filter applied - showing only Followed yields');
    }
  } catch (error) {
    Logger.log('Error in showFollowedYields: ' + error);
    SpreadsheetApp.getUi().alert('Error filtering followed yields: ' + error);
  }
}

/**
 * Helper function to parse filter values (handles empty, currency, percentages)
 * Returns null if empty/invalid (which means no limit)
 */
function parseFilterValue(value) {
  if (value === '' || value == null || value === undefined) {
    return null;  // Empty means no limit
  }
  
  // If it's already a number, return it
  if (typeof value === 'number') {
    return isNaN(value) ? null : value;
  }
  
  // Convert string to number (handle currency $ and % signs)
  const str = String(value).replace(/[$,%]/g, '').trim();
  const num = parseFloat(str);
  
  return isNaN(num) ? null : num;
}

/**
* Copy filtered data from Current sheet to Historical sheet
* Applies filters based on Historical sheet configuration
* Filters: C3 (Follow - "Follow" or "All"), D3 (Chain), E3 (Project), F3 (Symbol)
* Range filters: G2/G3 (TVL), H2/H3 (APY), I2/I3 (APY Base), J2/J3 (APY Reward), K2/K3 (Pool Meta)
*/
function copyToHistorical() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  try {
    const currentSheet = spreadsheet.getSheetByName('Current');
    const historicalSheet = spreadsheet.getSheetByName('Historical');
    
    if (!currentSheet) {
      throw new Error('Current sheet not found');
    }
    if (!historicalSheet) {
      throw new Error('Historical sheet not found');
    }
    
    // Show starting toast
    spreadsheet.toast('Starting to copy filtered data to Historical sheet...', 'Copy to Historical', 2);
    
    // Read filter configuration from Historical sheet (row 3)
    // Convert to string to handle numbers or other types from Google Sheets
    const followFilter = String(historicalSheet.getRange('C3').getValue() || '').trim();  // "Follow" or "All"
    const chainFilter = String(historicalSheet.getRange('D3').getValue() || '').trim();
    const projectFilter = String(historicalSheet.getRange('E3').getValue() || '').trim();
    const symbolFilter = String(historicalSheet.getRange('F3').getValue() || '').trim();
    
    // Read range filters (min from row 2, max from row 3)
    // Column mapping: G=TVL, H=APY, I=APY Base, J=APY Reward, K=Pool Meta
    // Parse values - empty cells will be null/empty string, which means no limit
    const tvlMinRaw = historicalSheet.getRange('G2').getValue();   // TVL (USD) min
    const tvlMaxRaw = historicalSheet.getRange('G3').getValue();   // TVL (USD) max
    const apyMinRaw = historicalSheet.getRange('H2').getValue();   // APY min
    const apyMaxRaw = historicalSheet.getRange('H3').getValue();   // APY max
    const apyBaseMinRaw = historicalSheet.getRange('I2').getValue();   // APY Base min
    const apyBaseMaxRaw = historicalSheet.getRange('I3').getValue();   // APY Base max
    const apyRewardMinRaw = historicalSheet.getRange('J2').getValue(); // APY Reward min
    const apyRewardMaxRaw = historicalSheet.getRange('J3').getValue(); // APY Reward max
    const poolMetaMinRaw = historicalSheet.getRange('K2').getValue();  // Pool Meta min
    const poolMetaMaxRaw = historicalSheet.getRange('K3').getValue();  // Pool Meta max
    
    // Convert to numbers (handle empty strings, percentages, currency)
    const tvlMin = parseFilterValue(tvlMinRaw);
    const tvlMax = parseFilterValue(tvlMaxRaw);
    const apyMin = parseFilterValue(apyMinRaw);
    const apyMax = parseFilterValue(apyMaxRaw);
    const apyBaseMin = parseFilterValue(apyBaseMinRaw);
    const apyBaseMax = parseFilterValue(apyBaseMaxRaw);
    const apyRewardMin = parseFilterValue(apyRewardMinRaw);
    const apyRewardMax = parseFilterValue(apyRewardMaxRaw);
    const poolMetaMin = parseFilterValue(poolMetaMinRaw);
    const poolMetaMax = parseFilterValue(poolMetaMaxRaw);
    
    Logger.log('Filters: Follow=' + followFilter + ', Chain=' + chainFilter + ', Project=' + projectFilter + ', Symbol=' + symbolFilter);
    Logger.log('TVL Raw: min=' + tvlMinRaw + ' (type: ' + typeof tvlMinRaw + '), max=' + tvlMaxRaw + ' (type: ' + typeof tvlMaxRaw + ')');
    Logger.log('TVL Range: ' + tvlMin + ' - ' + tvlMax);
    Logger.log('APY Range: ' + apyMin + ' - ' + apyMax);
    
    // Parse comma-separated filter values (convert to arrays, trim, lowercase for wildcard matching)
    // Helper to check if a filter value is "All" or empty
    const isAllValue = (val) => !val || val.trim().toLowerCase() === 'all';
    
    const chainFilters = isAllValue(chainFilter) ? [] : chainFilter.split(',').map(s => String(s).trim().toLowerCase()).filter(s => s.length > 0);
    const projectFilters = isAllValue(projectFilter) ? [] : projectFilter.split(',').map(s => String(s).trim().toLowerCase()).filter(s => s.length > 0);
    const symbolFilters = isAllValue(symbolFilter) ? [] : symbolFilter.split(',').map(s => String(s).trim().toLowerCase()).filter(s => s.length > 0);
    
    Logger.log('Parsed chainFilters: [' + chainFilters.join(', ') + ']');
    Logger.log('Parsed projectFilters: [' + projectFilters.join(', ') + ']');
    Logger.log('Parsed symbolFilters: [' + symbolFilters.join(', ') + ']');
    
    // Read data from Current sheet (starting from row 5)
    const currentLastRow = currentSheet.getLastRow();
    if (currentLastRow < 5) {
      Logger.log('No data in Current sheet');
      spreadsheet.toast('No data in Current sheet', 'Copy to Historical', 3);
      return;
    }
    
    Logger.log(`Reading data from Current sheet: ${currentLastRow - 4} rows`);
    
    // Read data rows from Current (row 5 onwards) in batches to avoid timeout
    // Read columns A through K (11 columns: Pool ID, Coin, Tracing, Chain, Project, Symbol, TVL, APY, APY Base, APY Reward, Pool Meta)
    const NUM_COLUMNS = 11;
    const BATCH_SIZE = 5000;  // Read 5000 rows at a time
    const totalRows = currentLastRow - 4;
    
    // Get current datetime
    const currentDateTime = new Date();
    
    // Filter and prepare rows for Historical sheet
    const filteredRows = [];
    let processedCount = 0;
    
    // Process data in batches
    for (let startRow = 5; startRow <= currentLastRow; startRow += BATCH_SIZE) {
      const batchSize = Math.min(BATCH_SIZE, currentLastRow - startRow + 1);
      const progressPercent = Math.round((startRow - 4) / totalRows * 100);
      Logger.log(`Reading batch: rows ${startRow} to ${startRow + batchSize - 1} (${progressPercent}% complete)...`);
      
      // Show progress toast every few batches
      if ((startRow - 5) % (BATCH_SIZE * 3) === 0) {
        spreadsheet.toast(`Reading data: ${progressPercent}% complete...`, 'Copy to Historical', 1);
      }
      
      const batchData = currentSheet.getRange(startRow, 1, batchSize, NUM_COLUMNS).getValues();
      
      // Log sample chain values from first batch for debugging
      if (startRow === 5 && batchData.length > 0) {
        const sampleChains = batchData.slice(0, 5).map(row => String(row[3] || '').trim()).filter(c => c);
        Logger.log('Sample chain values from first batch: ' + sampleChains.join(', '));
      }
      
      // Process each row in the batch
      batchData.forEach((row, index) => {
      processedCount++;
      // Log progress every 1000 rows to help debug if it hangs
      if (processedCount % 1000 === 0) {
        Logger.log(`Processing row ${processedCount} / ${totalRows}...`);
      }
      const poolId = String(row[0] || '').trim();  // Column A (index 0) - Pool ID
      const coin = String(row[1] || '').trim();  // Column B (index 1) - Coin
      const tracingStatus = String(row[2] || '').trim();  // Column C (index 2) - Tracing
      const chain = String(row[3] || '').trim();  // Column D (index 3) - Chain
      const project = String(row[4] || '').trim(); // Column E (index 4)
      const symbol = String(row[5] || '').trim();  // Column F (index 5)
      const tvl = parseFloat(row[6]) || 0;  // Column G (index 6) - TVL (USD)
      
      // Parse APY values (remove % sign if present, handle empty)
      const apyRaw = row[7];
      const apyStr = String(apyRaw || '').replace('%', '').trim();
      const apyIsEmpty = !apyRaw || apyStr === '' || isNaN(parseFloat(apyStr));
      const apy = apyIsEmpty ? null : (parseFloat(apyStr) || 0);
      
      const apyBaseRaw = row[8];
      const apyBaseStr = String(apyBaseRaw || '').replace('%', '').trim();
      const apyBaseIsEmpty = !apyBaseRaw || apyBaseStr === '' || isNaN(parseFloat(apyBaseStr));
      const apyBase = apyBaseIsEmpty ? null : (parseFloat(apyBaseStr) || 0);
      
      // Check if APY Reward is empty (before parsing)
      const apyRewardRaw = row[9];
      const apyRewardStr = String(apyRewardRaw || '').replace('%', '').trim();
      const apyRewardIsEmpty = !apyRewardRaw || apyRewardStr === '' || isNaN(parseFloat(apyRewardStr));
      const apyReward = apyRewardIsEmpty ? null : (parseFloat(apyRewardStr) || 0);
      
      // Check if Pool Meta is empty (before parsing)
      const poolMetaRaw = row[10];
      const poolMetaStr = String(poolMetaRaw || '').trim();
      const poolMetaIsEmpty = !poolMetaRaw || poolMetaStr === '' || isNaN(parseFloat(poolMetaStr));
      const poolMeta = poolMetaIsEmpty ? null : (parseFloat(poolMetaStr) || 0);
      
      // Apply filters
      let passesFilter = true;
      
      // Follow filter (if set to "Follow", only include rows with Follow status)
      if (followFilter && followFilter.trim().toLowerCase() === 'follow') {
        if (tracingStatus !== 'Follow') {
          passesFilter = false;
        }
      }
      // If followFilter is "All" or empty, include all rows regardless of Tracing status
      
      // Chain filter (wildcard match)
      if (chainFilters.length > 0 && passesFilter) {
        const chainLower = chain.toLowerCase();
        const matches = chainFilters.some(filter => chainLower.includes(filter));
        // Debug logging for first few matches/non-matches
        if (processedCount <= 10) {
          Logger.log(`Row ${processedCount}: chain="${chain}" (lowercase: "${chainLower}") matches filters [${chainFilters.join(', ')}]: ${matches}`);
        }
        if (!matches) {
          passesFilter = false;
        }
      }
      
      // Project filter (wildcard match)
      if (projectFilters.length > 0 && passesFilter) {
        const projectLower = project.toLowerCase();
        passesFilter = passesFilter && projectFilters.some(filter => projectLower.includes(filter));
      }
      
      // Symbol filter (wildcard match)
      if (symbolFilters.length > 0 && passesFilter) {
        const symbolLower = symbol.toLowerCase();
        passesFilter = passesFilter && symbolFilters.some(filter => symbolLower.includes(filter));
      }
      
      // TVL range filter (null min/max means no limit)
      if (passesFilter) {
        if (tvlMin != null) {
          if (tvl < tvlMin) {
            // Debug logging for first few TVL filter failures
            if (processedCount <= 10) {
              Logger.log(`Row ${processedCount}: TVL ${tvl} < min ${tvlMin} - filtering out`);
            }
            passesFilter = false;
          } else if (processedCount <= 5) {
            Logger.log(`Row ${processedCount}: TVL ${tvl} >= min ${tvlMin} - passing`);
          }
        }
        if (tvlMax != null && passesFilter && tvl > tvlMax) {
          if (processedCount <= 10) {
            Logger.log(`Row ${processedCount}: TVL ${tvl} > max ${tvlMax} - filtering out`);
          }
          passesFilter = false;
        }
      }
      
      // APY range filter (special case: if APY is empty, always pass - ignore filter)
      // Empty APY means "no APY data" which is a valid state that should always be copied
      if (passesFilter && !apyIsEmpty) {
        // Only apply filter if APY has a value
        if (apyMin != null && apy < apyMin) passesFilter = false;
        if (apyMax != null && apy > apyMax) passesFilter = false;
      }
      // If apyIsEmpty is true, skip the filter check (always pass)
      
      // APY Base range filter (special case: if APY Base is empty, always pass - ignore filter)
      // Empty APY Base means "no base APY data" which is a valid state that should always be copied
      if (passesFilter && !apyBaseIsEmpty) {
        // Only apply filter if APY Base has a value
        if (apyBaseMin != null && apyBase < apyBaseMin) passesFilter = false;
        if (apyBaseMax != null && apyBase > apyBaseMax) passesFilter = false;
      }
      // If apyBaseIsEmpty is true, skip the filter check (always pass)
      
      // APY Reward range filter (special case: if APY Reward is empty, always pass - ignore filter)
      // Empty APY Reward means "no rewards" which is a valid state that should always be copied
      if (passesFilter && !apyRewardIsEmpty) {
        // Only apply filter if APY Reward has a value
        if (apyRewardMin != null && apyReward < apyRewardMin) passesFilter = false;
        if (apyRewardMax != null && apyReward > apyRewardMax) passesFilter = false;
      }
      // If apyRewardIsEmpty is true, skip the filter check (always pass)
      
      // Pool Meta range filter (special case: if Pool Meta is empty, always pass - ignore filter)
      if (passesFilter && !poolMetaIsEmpty) {
        if (poolMetaMin != null && poolMeta < poolMetaMin) passesFilter = false;
        if (poolMetaMax != null && poolMeta > poolMetaMax) passesFilter = false;
      }
      
      // If row passes all filters, add it to filtered rows
      if (passesFilter) {
        // Prepare row: datetime, Coin, Pool ID, Tracing, Chain, Project, Symbol, TVL, APY, APY Base, APY Reward, Pool Meta
        filteredRows.push([
          currentDateTime,  // Column A: datetime
          coin,             // Column B: Coin
          poolId,           // Column C: Pool ID
          tracingStatus,    // Column D: Tracing (Follow/Don't follow)
          chain,            // Column E: Chain
          project,          // Column F: Project
          symbol,           // Column G: Symbol
          tvl,              // Column H: TVL (USD)
          apy,              // Column I: APY
          apyBase,          // Column J: APY Base
          apyRewardIsEmpty ? '' : apyReward,  // Column K: APY Reward (empty string if no rewards)
          poolMetaIsEmpty ? '' : poolMeta     // Column L: Pool Meta (empty string if none)
        ]);
      }
      });
      
      // Small delay between batches to avoid rate limits
      if (startRow + BATCH_SIZE <= currentLastRow) {
        Utilities.sleep(100);
      }
    }
    
    Logger.log(`Filtered ${filteredRows.length} rows from ${totalRows} total rows (processed ${processedCount} rows)`);
    if (chainFilters.length > 0) {
      Logger.log(`Chain filter applied: [${chainFilters.join(', ')}] - found ${filteredRows.length} matching rows`);
    }
    
    // Find last row in Historical sheet (data starts at row 5)
    const historicalLastRow = historicalSheet.getLastRow();
    const startRow = Math.max(5, historicalLastRow + 1);  // Start at row 5 or after last data row
    
    // Append filtered rows to Historical sheet
    if (filteredRows.length > 0) {
      historicalSheet.getRange(startRow, 1, filteredRows.length, filteredRows[0].length).setValues(filteredRows);
      Logger.log(`Successfully copied ${filteredRows.length} rows to Historical sheet starting at row ${startRow}`);
      spreadsheet.toast(`Successfully copied ${filteredRows.length.toLocaleString()} rows to Historical sheet`, 'Copy to Historical - Complete', 5);
    } else {
      Logger.log('No rows matched the filter criteria');
      spreadsheet.toast('No rows matched the filter criteria', 'Copy to Historical', 3);
    }
    
  } catch (error) {
    Logger.log('Error in copyToHistorical: ' + error);
    spreadsheet.toast('Error: ' + error, 'Copy to Historical - Error', 5);
    SpreadsheetApp.getUi().alert('Error copying to Historical: ' + error);
  }
}

