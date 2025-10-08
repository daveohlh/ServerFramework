# Database Architecture Optimization Issues - JSON-driven script
# Following storied_and_scoped.yml format

Write-Host "Starting database optimization issues creation script..." -ForegroundColor Green

# Helper function to check if issue already exists
function Get-ExistingIssue {
    param($Title)
    try {
        Write-Host "    Checking for existing issue: '$Title'" -ForegroundColor Gray
        
        # Get ALL issues without pagination - force a very high limit to ensure we get everything
        # We'll get both open and closed to avoid any duplicates
        $existingIssues = gh issue list --repo "JamesonRGrieve/ServerFramework" --state all --limit 1000 --json "number,title,state" | ConvertFrom-Json
        
        if (-not $existingIssues) {
            Write-Host "    No issues found in repository" -ForegroundColor Gray
            return $null
        }
        
        Write-Host "    Retrieved $($existingIssues.Count) total issues from repository" -ForegroundColor Gray
        
        # Normalize titles for comparison - trim whitespace
        $searchTitle = $Title.Trim()
        
        # Check for exact title match (case-sensitive to match GitHub behavior)
        $matchingIssues = $existingIssues | Where-Object { 
            $_.title.Trim() -eq $searchTitle
        }
        
        if ($matchingIssues) {
            Write-Host "    ✓ Found $($matchingIssues.Count) matching issue(s)" -ForegroundColor Yellow
            
            # Prefer open issues over closed ones
            $openMatches = $matchingIssues | Where-Object { $_.state -eq "open" }
            if ($openMatches) {
                if ($openMatches.Count -gt 1) {
                    $lowestNumber = ($openMatches | Sort-Object number)[0].number
                    Write-Host "    → Using oldest open issue #$lowestNumber" -ForegroundColor Yellow
                    return $lowestNumber
                }
                else {
                    Write-Host "    → Using open issue #$($openMatches.number)" -ForegroundColor Yellow
                    return $openMatches.number
                }
            }
            else {
                # All matches are closed, use the newest closed one
                $newestClosed = ($matchingIssues | Sort-Object number -Descending)[0].number
                Write-Host "    → Using newest closed issue #$newestClosed" -ForegroundColor Yellow
                return $newestClosed
            }
        }
        
        Write-Host "    ✗ No matching issues found" -ForegroundColor Gray
        return $null
    }
    catch {
        Write-Host "    ERROR: Failed to check existing issues: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Helper function to create or get existing issue
function Create-OrGetIssue {
    param($Title, $Body)
    
    $existingNumber = Get-ExistingIssue $Title
    
    if ($existingNumber) {
        Write-Host "  ↻ Updating existing issue #$existingNumber" -ForegroundColor Yellow
        try {
            gh issue edit $existingNumber --repo "JamesonRGrieve/ServerFramework" --body $Body 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ Successfully updated issue #$existingNumber" -ForegroundColor Green
            }
            else {
                Write-Host "  ⚠ Warning: Update may have failed for issue #$existingNumber" -ForegroundColor Yellow
            }
            return $existingNumber
        }
        catch {
            Write-Host "  ⚠ Warning: Failed to update issue #$existingNumber - $($_.Exception.Message)" -ForegroundColor Yellow
            return $existingNumber
        }
    }
    
    # Manual confirmation before creating new issue
    Write-Host ""
    Write-Host "  MANUAL CONFIRMATION REQUIRED:" -ForegroundColor Yellow
    Write-Host "  About to create new issue: '$Title'" -ForegroundColor Cyan
    Write-Host "  Repository: JamesonRGrieve/ServerFramework" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Do you want to create this issue? (y/n/s for skip):" -ForegroundColor Yellow
    $confirmation = Read-Host "  "
    
    if ($confirmation -eq "s" -or $confirmation -eq "S") {
        Write-Host "  → Skipped creating issue" -ForegroundColor Yellow
        return "SKIPPED"
    }
    
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-Host "  → Cancelled issue creation" -ForegroundColor Yellow
        return $null
    }
    
    Write-Host "  + Creating new issue..." -ForegroundColor Cyan
    try {
        $issueUrl = gh issue create --repo "JamesonRGrieve/ServerFramework" --title $Title --body $Body 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $issueUrl -match '/issues/(\d+)') { 
            $newNumber = $Matches[1]
            Write-Host "  ✓ Created new issue #$newNumber" -ForegroundColor Green
            return $newNumber
        }
        else {
            Write-Host "  ✗ Failed to create issue. Output: $issueUrl" -ForegroundColor Red
            return $null
        }
    }
    catch {
        Write-Host "  ✗ Exception creating issue: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Helper function to add issue to project board
function Add-IssueToProject {
    param($IssueNumber)
    try {
        # First try to add the issue
        $addResult = gh project item-add 4 --owner JamesonRGrieve --url "https://github.com/JamesonRGrieve/ServerFramework/issues/$IssueNumber" 2>&1
        
        if ($addResult -like "*missing required scopes*") {
            Write-Host "  → Project scope missing - skipping project board" -ForegroundColor Yellow
            return
        }
        
        if ($addResult -like "*already exists*" -or $addResult -like "*already added*") {
            Write-Host "  → Already on project board" -ForegroundColor Green
            return
        }
        
        # Give GitHub a moment to process the addition
        Start-Sleep -Seconds 1
        
        # Try to set status without verbose output
        $itemList = gh project item-list 4 --owner JamesonRGrieve --format json 2>$null
        if ($itemList -and $itemList -notlike "*error*") {
            $items = $itemList | ConvertFrom-Json
            $targetItem = $items | Where-Object { $_.content.number -eq $IssueNumber }
            
            if ($targetItem) {
                gh project item-edit --id $targetItem.id --field-id "Status" --single-select-option-id "To-Do" 2>$null
                Write-Host "  → Added to project board with To-Do status" -ForegroundColor Green
            }
            else {
                Write-Host "  → Added to project board (status not set)" -ForegroundColor Green
            }
        }
        else {
            Write-Host "  → Added to project board (status unknown)" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "  → Project board error (issue still processed)" -ForegroundColor Yellow
    }
}

Write-Host "Testing GitHub CLI authentication..." -ForegroundColor Yellow
try {
    $authStatus = gh auth status 2>&1
    Write-Host "GitHub CLI auth status: $authStatus" -ForegroundColor Cyan
    
    # Check if project scope is available - look for 'project' in the token scopes line
    $hasProjectScope = $authStatus -match "project"
    if (-not $hasProjectScope) {
        Write-Host "WARNING: Project scope not detected in token scopes" -ForegroundColor Yellow
        Write-Host "Project board integration may not work. To fix this, run:" -ForegroundColor Yellow
        Write-Host "  gh auth refresh -s project" -ForegroundColor Cyan
        Write-Host "Issues will still be created successfully." -ForegroundColor Green
        Write-Host ""
    }
    else {
        Write-Host "SUCCESS: Project scope detected - project board integration enabled" -ForegroundColor Green
        Write-Host ""
    }
}
catch {
    Write-Host "GitHub CLI authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Creating issues..." -ForegroundColor Green

# Load issues from JSON file
Write-Host "Loading issues from issues.json..." -ForegroundColor Yellow
try {
    $jsonPath = Join-Path $PSScriptRoot "issues.json"
    if (-not (Test-Path $jsonPath)) {
        Write-Host "ERROR: issues.json file not found at $jsonPath" -ForegroundColor Red
        exit 1
    }
    
    $issuesData = Get-Content $jsonPath -Raw | ConvertFrom-Json
    $totalIssues = $issuesData.issues.Count
    Write-Host "SUCCESS: Loaded $totalIssues issues from JSON" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "ERROR: Failed to load issues.json: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Process all issues from JSON
$processedIssues = @()
$skippedIssues = @()
$batchSize = 5
$currentBatch = 1

for ($i = 0; $i -lt $issuesData.issues.Count; $i++) {
    $issue = $issuesData.issues[$i]
    $issueNumber = $i + 1
    $title = $issue.title
    $body = $issue.body
    
    Write-Host "$issueNumber. $title" -ForegroundColor Cyan
    
    $githubIssueNumber = Create-OrGetIssue $title $body
    
    if ($githubIssueNumber -eq "SKIPPED") {
        $skippedIssues += @{
            number = $issueNumber
            title  = $title
        }
    }
    elseif ($githubIssueNumber) {
        Add-IssueToProject $githubIssueNumber
        $processedIssues += @{
            number       = $issueNumber
            title        = $title
            githubNumber = $githubIssueNumber
        }
    }
    
    # Progress indicator and batching
    if (($i + 1) % $batchSize -eq 0 -and ($i + 1) -lt $issuesData.issues.Count) {
        $remaining = $issuesData.issues.Count - ($i + 1)
        Write-Host ""
        Write-Host "Batch $currentBatch completed! $remaining issues remaining..." -ForegroundColor Green
        Write-Host "Continue with next batch? (y/n):" -ForegroundColor Yellow
        $continue = Read-Host
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Host "Stopping at user request." -ForegroundColor Yellow
            break
        }
        Write-Host ""
        $currentBatch++
    }
}

Write-Host ""
Write-Host "Issue processing completed!" -ForegroundColor Green
Write-Host "Repository: JamesonRGrieve/ServerFramework" -ForegroundColor Cyan
Write-Host ""

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Total Processed: $($processedIssues.Count) issues" -ForegroundColor Green
if ($skippedIssues.Count -gt 0) {
    Write-Host "  Total Skipped: $($skippedIssues.Count) issues" -ForegroundColor Yellow
}

# Check project scope one more time for final message
$finalAuthCheck = gh auth status 2>&1
if ($finalAuthCheck -notmatch "project") {
    Write-Host ""
    Write-Host "Note: To enable automatic project board integration, run:" -ForegroundColor Yellow
    Write-Host "  gh auth refresh -s project" -ForegroundColor Cyan
} 