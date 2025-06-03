import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { v4 as uuidv4 } from 'uuid';
import { Query } from '../../models/query.model';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { QueryComponent } from '../../components/query/query/query.component';
import { API } from '../../../environments/api';

const API_BASE = API.Base;

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, QueryComponent, MatProgressSpinnerModule],
  templateUrl: './search.page.html',
  styleUrls: ['./search.page.scss'],
})
export class SearchPage {
  private readonly http = inject(HttpClient);

  isLoading = false;
  statusText = '';

  async startSearch(query: Query): Promise<void> {
    this.isLoading = true;
    this.statusText = 'Uploading images...';

    const searchId = uuidv4();

    try {
      await Promise.all(
        query.images.map((file) => {
          const url = `${API_BASE}/fetch/${searchId}/upload/${encodeURIComponent(file.name)}`;
          const headers = new HttpHeaders({ 'Content-Type': file.type });
          return firstValueFrom(this.http.put(url, file, { headers }));
        }),
      );

      this.statusText = 'All images uploaded. Starting search...';

      // TODO: trigger next API call using the query + searchId
    } catch (error) {
      console.error('Image upload failed', error);
      this.statusText = 'Failed to upload images.';
    } finally {
      this.isLoading = false;
    }
  }
}
