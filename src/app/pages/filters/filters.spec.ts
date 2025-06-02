import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FiltersPage } from './filters.page';

describe('Filters', () => {
  let component: FiltersPage;
  let fixture: ComponentFixture<FiltersPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FiltersPage],
    }).compileComponents();

    fixture = TestBed.createComponent(FiltersPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
