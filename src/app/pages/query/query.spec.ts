import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QueryPage } from './query.page';

describe('Query', () => {
  let component: QueryPage;
  let fixture: ComponentFixture<QueryPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QueryPage],
    }).compileComponents();

    fixture = TestBed.createComponent(QueryPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
